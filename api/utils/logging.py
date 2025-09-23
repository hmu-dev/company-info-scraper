import logging
import json
import time
from datetime import datetime
from functools import wraps
from typing import Any, Dict, Optional
import boto3

# Configure logging
logger = logging.getLogger("ai_web_scraper")
logger.setLevel(logging.INFO)

# CloudWatch client
cloudwatch = boto3.client("cloudwatch")


def log_event(
    event_type: str, data: Dict[str, Any], request_id: Optional[str] = None
) -> None:
    """Log a structured event to CloudWatch"""
    log_data = {
        "event_type": event_type,
        "timestamp": datetime.now().isoformat(),
        "request_id": request_id,
        "data": data,
    }
    logger.info(json.dumps(log_data))


def publish_metrics(namespace: str, metrics: Dict[str, tuple]) -> None:
    """Publish metrics to CloudWatch"""
    try:
        metric_data = [
            {
                "MetricName": name,
                "Value": value,
                "Unit": unit,
                "Timestamp": datetime.now(),
            }
            for name, (value, unit) in metrics.items()
        ]

        cloudwatch.put_metric_data(Namespace=namespace, MetricData=metric_data)
    except Exception as e:
        logger.error(f"Failed to publish metrics: {str(e)}")


def track_request(func):
    """Decorator to track request metrics and logging"""

    @wraps(func)
    def wrapper(event, context):
        request_id = context.aws_request_id
        start_time = time.time()

        # Log request start
        log_event(
            "request_start",
            {
                "url": event.get("url"),
                "model": event.get("model", "gpt-3.5-turbo"),
                "api_version": "1.0",
            },
            request_id,
        )

        try:
            # Execute function
            result = func(event, context)

            # Calculate duration
            duration = time.time() - start_time

            # Log success metrics
            metrics = {
                "RequestDuration": (duration, "Seconds"),
                "SuccessfulRequests": (1, "Count"),
            }

            # Add LLM metrics if available
            if isinstance(result, dict) and "token_usage" in result:
                metrics.update({"TokensUsed": (result["token_usage"], "Count")})

            # Publish metrics
            publish_metrics("AiWebScraper", metrics)

            # Log request end
            log_event(
                "request_end",
                {"duration": duration, "success": True, "metrics": metrics},
                request_id,
            )

            return result

        except Exception as e:
            # Calculate duration even for failures
            duration = time.time() - start_time

            # Log error metrics
            metrics = {
                "RequestDuration": (duration, "Seconds"),
                "FailedRequests": (1, "Count"),
                "Errors": (1, "Count"),
            }

            # Publish error metrics
            publish_metrics("AiWebScraper", metrics)

            # Log error details
            log_event(
                "request_error",
                {"error": str(e), "error_type": type(e).__name__, "duration": duration},
                request_id,
            )

            raise

    return wrapper


def log_llm_request(llm_data: Dict[str, Any], request_id: Optional[str] = None) -> None:
    """Log LLM interaction details"""
    log_event(
        "llm_interaction",
        {
            "model": llm_data["model"],
            "prompt_tokens": llm_data["prompt_tokens"],
            "completion_tokens": llm_data["completion_tokens"],
            "duration": llm_data["duration"],
            "success": llm_data["success"],
        },
        request_id,
    )

    # Publish LLM metrics
    metrics = {
        "LLMLatency": (llm_data["duration"], "Seconds"),
        "PromptTokens": (llm_data["prompt_tokens"], "Count"),
        "CompletionTokens": (llm_data["completion_tokens"], "Count"),
        "TotalTokens": (
            llm_data["prompt_tokens"] + llm_data["completion_tokens"],
            "Count",
        ),
    }
    publish_metrics("AiWebScraper", metrics)


def log_media_metrics(
    media_data: Dict[str, Any], request_id: Optional[str] = None
) -> None:
    """Log media processing metrics"""
    log_event(
        "media_processing",
        {
            "url": media_data["url"],
            "type": media_data["type"],
            "size_bytes": media_data["size"],
            "processing_time": media_data["duration"],
            "success": media_data["success"],
        },
        request_id,
    )

    # Publish media metrics
    metrics = {
        "MediaProcessingTime": (media_data["duration"], "Seconds"),
        "MediaSize": (media_data["size"], "Bytes"),
        f"{media_data['type'].capitalize()}Count": (1, "Count"),
    }
    publish_metrics("AiWebScraper", metrics)


def log_cache_metrics(
    cache_data: Dict[str, Any], request_id: Optional[str] = None
) -> None:
    """Log cache interaction metrics"""
    log_event(
        "cache_interaction",
        {
            "operation": cache_data["operation"],
            "success": cache_data["success"],
            "duration": cache_data["duration"],
        },
        request_id,
    )

    # Publish cache metrics
    metrics = {
        "CacheLatency": (cache_data["duration"], "Seconds"),
        f"Cache{cache_data['operation']}s": (1, "Count"),
    }
    if cache_data["operation"] == "Hit":
        metrics["CacheHits"] = (1, "Count")
    elif cache_data["operation"] == "Miss":
        metrics["CacheMisses"] = (1, "Count")

    publish_metrics("AiWebScraper", metrics)
