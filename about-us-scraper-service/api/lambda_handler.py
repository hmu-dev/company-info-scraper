import json
from typing import Any, Dict

from fastapi import FastAPI

# Import your FastAPI app
from main import app
from mangum import Mangum

# Temporarily disabled for basic deployment
# from utils.logging import (
#     log_cache_metrics,
#     log_llm_request,
#     log_media_metrics,
#     track_request,
# )

# Create Lambda handler
handler = Mangum(app)


# Simplified handler for basic deployment
def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Simplified AWS Lambda handler for the AI Web Scraper API
    """
    try:
        # Process the request through FastAPI/Mangum
        response = handler(event, context)
        return response

    except Exception as e:
        # Return a proper error response
        error_response = {
            "statusCode": 500,
            "body": json.dumps(
                {"success": False, "error": str(e), "error_type": type(e).__name__}
            ),
        }
        return error_response
