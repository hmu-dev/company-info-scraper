import json
from typing import Any, Dict

from fastapi import FastAPI
from mangum import Mangum

# Import your FastAPI app
from .main import app
from .utils.logging import (
    log_cache_metrics,
    log_llm_request,
    log_media_metrics,
    track_request,
)

# Create Lambda handler
handler = Mangum(app)


# Wrap the handler with our logging decorator
@track_request
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for the AI Web Scraper API

    This handler:
    1. Processes API Gateway events
    2. Tracks request metrics
    3. Handles errors gracefully
    4. Returns properly formatted responses
    """
    try:
        # Process the request through FastAPI/Mangum
        response = handler(event, context)

        # Extract response data for metrics
        if isinstance(response.get("body"), str):
            body = json.loads(response["body"])

            # Log LLM metrics if available
            if "token_usage" in body:
                log_llm_request(
                    {
                        "model": body.get("model", "gpt-3.5-turbo"),
                        "prompt_tokens": body["token_usage"].get("prompt_tokens", 0),
                        "completion_tokens": body["token_usage"].get(
                            "completion_tokens", 0
                        ),
                        "duration": body.get("duration", 0),
                        "success": body.get("success", True),
                    },
                    context.aws_request_id,
                )

            # Log media metrics if available
            if "media" in body:
                for media_item in body["media"]:
                    log_media_metrics(
                        {
                            "url": media_item["url"],
                            "type": media_item["type"],
                            "size": media_item.get("metadata", {}).get("size_bytes", 0),
                            "duration": body.get("duration", 0),
                            "success": True,
                        },
                        context.aws_request_id,
                    )

            # Log cache metrics if available
            if "cache_info" in body:
                log_cache_metrics(
                    {
                        "operation": "Hit" if body["cache_info"]["hit"] else "Miss",
                        "success": True,
                        "duration": body["cache_info"].get("duration", 0),
                    },
                    context.aws_request_id,
                )

        return response

    except Exception as e:
        # Log the error and return a proper error response
        error_response = {
            "statusCode": 500,
            "body": json.dumps(
                {"success": False, "error": str(e), "error_type": type(e).__name__}
            ),
        }
        return error_response
