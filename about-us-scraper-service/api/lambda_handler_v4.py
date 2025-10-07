"""
AWS Lambda handler for AI Web Scraper API - Version 4.0
Matches remote development team schema requirements.
"""

import json
from typing import Any, Dict

from main_v4 import app
from mangum import Mangum

handler = Mangum(app)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for the AI Web Scraper API v4.0
    Compatible with remote development team schema requirements.
    """
    try:
        # Process the request through FastAPI/Mangum
        response = handler(event, context)
        return response

    except Exception as e:
        # Return a proper error response matching the expected schema
        error_response = {
            "statusCode": 500,
            "message": f"Internal server error: {str(e)}",
            "scrapingData": None,
        }
        return error_response


