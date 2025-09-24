from typing import Any, Dict
from main_hybrid import app
from mangum import Mangum

# Create Lambda handler
handler = Mangum(app)

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda handler for the Hybrid AI Web Scraper API
    
    Features:
    - ⚡ Fast programmatic extraction
    - 🧠 Smart AI fallback
    - 🔍 Auto-discovery of About pages
    - 📸 Complete media asset extraction
    """
    try:
        response = handler(event, context)
        return response
    except Exception as e:
        return {
            "statusCode": 500,
            "body": f'{{"success": false, "error": "{str(e)}", "error_type": "{type(e).__name__}"}}'
        }
