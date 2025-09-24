import json
from typing import Any, Dict

from main_split import app
from mangum import Mangum

handler = Mangum(app)

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    try:
        response = handler(event, context)
        return response
    except Exception as e:
        error_response = {
            "statusCode": 500,
            "body": json.dumps(
                {"success": False, "error": str(e), "error_type": type(e).__name__}
            ),
        }
        return error_response
