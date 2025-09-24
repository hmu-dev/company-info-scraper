from typing import Any, Dict
from main_with_scraping import app
from mangum import Mangum

# Create Lambda handler
handler = Mangum(app)

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for the AI Web Scraper API with scraping capabilities
    """
    try:
        response = handler(event, context)
        return response
    except Exception as e:
        return {
            "statusCode": 500,
            "body": f'{{"success": false, "error": "{str(e)}"}}'
        }
