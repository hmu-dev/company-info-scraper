from typing import Any, Dict

from main_simple import app
from mangum import Mangum

# Create Lambda handler
handler = Mangum(app)


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Simplified AWS Lambda handler
    """
    try:
        response = handler(event, context)
        return response
    except Exception as e:
        return {"statusCode": 500, "body": f'{{"error": "{str(e)}"}}'}
