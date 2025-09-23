"""
Logging utilities for the API.

This module provides functions for logging events and publishing metrics
to CloudWatch.
"""

import json
import time
from datetime import datetime
from functools import wraps
from typing import Any, Dict, List, Optional

import boto3


def track_request(func):
    """
    Decorator to track request metrics.

    Args:
        func: The function to wrap

    Returns:
        The wrapped function
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            response = func(*args, **kwargs)
            duration = time.time() - start_time
            log_event(
                "request_success",
                {
                    "duration": duration,
                    "path": args[0].get("path"),
                    "method": args[0].get("httpMethod"),
                },
                args[1].aws_request_id if len(args) > 1 else None,
            )
            publish_metrics(
                [{"name": "RequestDuration", "value": duration, "unit": "Seconds"}]
            )
            return response
        except Exception as e:
            duration = time.time() - start_time
            log_event(
                "request_error",
                {
                    "duration": duration,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "path": args[0].get("path"),
                    "method": args[0].get("httpMethod"),
                },
                args[1].aws_request_id if len(args) > 1 else None,
            )
            publish_metrics([{"name": "Errors", "value": 1, "unit": "Count"}])
            raise

    return wrapper


def log_event(
    event_type: str, data: Dict[str, Any], request_id: Optional[str] = None
) -> None:
    """
    Log an event with structured data.

    Args:
        event_type: Type of event
        data: Event data
        request_id: Optional request ID
    """
    event = {
        "event_type": event_type,
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": request_id,
        "data": data,
    }
    print(json.dumps(event))


def publish_metrics(
    metrics: List[Dict[str, Any]], namespace: str = "AboutUsScraper"
) -> None:
    """
    Publish metrics to CloudWatch.

    Args:
        metrics: List of metrics to publish
        namespace: CloudWatch namespace

    Each metric should have:
        - name: Metric name
        - value: Metric value
        - unit: Metric unit (Count, Seconds, Bytes, etc.)
    """
    try:
        cloudwatch = boto3.client("cloudwatch")
        metric_data = []
        for metric in metrics:
            metric_data.append(
                {
                    "MetricName": metric["name"],
                    "Value": metric["value"],
                    "Unit": metric["unit"],
                }
            )
        cloudwatch.put_metric_data(Namespace=namespace, MetricData=metric_data)
    except Exception as e:
        log_event("metric_error", {"error": str(e)})


def log_llm_request(data: Dict[str, Any], request_id: Optional[str] = None) -> None:
    """
    Log LLM request metrics.

    Args:
        data: LLM request data
        request_id: Optional request ID
    """
    log_event(
        "llm_success" if data.get("success", True) else "llm_error", data, request_id
    )
    if data.get("success", True):
        publish_metrics(
            [
                {
                    "name": "PromptTokens",
                    "value": data.get("prompt_tokens", 0),
                    "unit": "Count",
                },
                {
                    "name": "CompletionTokens",
                    "value": data.get("completion_tokens", 0),
                    "unit": "Count",
                },
                {
                    "name": "LLMLatency",
                    "value": data.get("duration", 0),
                    "unit": "Seconds",
                },
            ]
        )


def log_media_metrics(data: Dict[str, Any], request_id: Optional[str] = None) -> None:
    """
    Log media processing metrics.

    Args:
        data: Media processing data
        request_id: Optional request ID
    """
    log_event(
        "media_success" if data.get("success", True) else "media_error",
        data,
        request_id,
    )
    if data.get("success", True):
        publish_metrics(
            [
                {
                    "name": "MediaProcessingTime",
                    "value": data.get("duration", 0),
                    "unit": "Seconds",
                },
                {"name": "MediaSize", "value": data.get("size", 0), "unit": "Bytes"},
            ]
        )


def log_cache_metrics(
    operation: str, hit: bool, latency: float, request_id: Optional[str] = None
) -> None:
    """
    Log cache operation metrics.

    Args:
        operation: Cache operation (get, set, delete)
        hit: Whether the operation was a hit
        latency: Operation latency in seconds
        request_id: Optional request ID
    """
    data = {"operation": operation, "hit": hit, "latency": latency}
    log_event("cache_operation", data, request_id)
    publish_metrics(
        [
            {
                "name": "CacheHits" if hit else "CacheMisses",
                "value": 1,
                "unit": "Count",
            },
            {"name": "CacheLatency", "value": latency, "unit": "Seconds"},
        ]
    )
