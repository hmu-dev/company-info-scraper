import html
import re
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import validators
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from ..utils.logging import log_event


class RequestValidator:
    def __init__(
        self,
        max_url_length: int = 2048,
        allowed_schemes: List[str] = None,
        blocked_domains: List[str] = None,
        max_content_length: int = 10 * 1024 * 1024,
    ):  # 10MB
        """
        Initialize request validator

        Args:
            max_url_length: Maximum allowed URL length
            allowed_schemes: List of allowed URL schemes (e.g., http, https)
            blocked_domains: List of blocked domains
            max_content_length: Maximum allowed content length
        """
        self.max_url_length = max_url_length
        self.allowed_schemes = allowed_schemes or ["http", "https"]
        self.blocked_domains = blocked_domains or []
        self.max_content_length = max_content_length

    def validate_url(self, url: str) -> Optional[str]:
        """
        Validate URL

        Returns:
            Error message if validation fails, None if valid
        """
        # Check URL length
        if len(url) > self.max_url_length:
            return f"URL length exceeds maximum of {self.max_url_length} characters"

        # Basic URL validation
        if not validators.url(url):
            return "Invalid URL format"

        # Parse URL
        try:
            parsed = urlparse(url)

            # Check scheme
            if parsed.scheme not in self.allowed_schemes:
                return f"URL scheme must be one of: {', '.join(self.allowed_schemes)}"

            # Check domain
            domain = parsed.netloc.lower()
            if domain in self.blocked_domains:
                return "Access to this domain is blocked"

            # Check for common attack patterns
            if any(char in url for char in ["<", ">", '"', "'", ";", "(", ")"]):
                return "URL contains invalid characters"

        except Exception as e:
            return f"URL parsing failed: {str(e)}"

        return None

    def sanitize_string(self, value: str) -> str:
        """Sanitize string input"""
        # HTML escape
        value = html.escape(value)

        # Remove control characters
        value = "".join(char for char in value if ord(char) >= 32)

        # Normalize whitespace
        value = " ".join(value.split())

        return value

    def validate_api_key(self, api_key: Optional[str]) -> Optional[str]:
        """
        Validate API key format

        Returns:
            Error message if validation fails, None if valid
        """
        if not api_key:
            return None

        # Check length
        if len(api_key) < 32:
            return "API key is too short"

        # Check format (example: sk-...)
        if not re.match(r"^sk-[a-zA-Z0-9]{32,}$", api_key):
            return "Invalid API key format"

        return None

    def validate_content_length(self, length: int) -> Optional[str]:
        """
        Validate content length

        Returns:
            Error message if validation fails, None if valid
        """
        if length > self.max_content_length:
            return f"Content length exceeds maximum of {self.max_content_length} bytes"

        return None

    def validate_request_body(self, body: Dict[str, Any]) -> Optional[str]:
        """
        Validate request body

        Returns:
            Error message if validation fails, None if valid
        """
        # Check required fields
        required_fields = ["url"]
        missing_fields = [field for field in required_fields if field not in body]
        if missing_fields:
            return f"Missing required fields: {', '.join(missing_fields)}"

        # Validate URL
        url_error = self.validate_url(body["url"])
        if url_error:
            return url_error

        # Validate API key if present
        if "openai_api_key" in body:
            api_key_error = self.validate_api_key(body["openai_api_key"])
            if api_key_error:
                return api_key_error

        # Validate model name if present
        if "model" in body:
            model = body["model"]
            if not isinstance(model, str) or not re.match(r"^[a-zA-Z0-9-]+$", model):
                return "Invalid model name format"

        return None


class ValidationMiddleware:
    def __init__(self, app, validator: RequestValidator):
        """Initialize validation middleware"""
        self.app = app
        self.validator = validator

    async def __call__(self, scope, receive, send):
        """Process request with validation"""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        from fastapi import Request

        request = Request(scope, receive)

        async def call_next(request):
            async def send_wrapper(message):
                await send(message)

            return await self.app(scope, receive, send_wrapper)

        try:
            # Validate content length
            content_length = request.headers.get("content-length")
            if content_length:
                error = self.validator.validate_content_length(int(content_length))
                if error:
                    log_event(
                        "validation_error", {"type": "content_length", "error": error}
                    )
                    response = JSONResponse(status_code=413, content={"error": error})
                    await response(scope, receive, send)
                    return

            # For POST/PUT requests, validate body
            if request.method in ["POST", "PUT"]:
                try:
                    body = await request.json()
                    error = self.validator.validate_request_body(body)
                    if error:
                        log_event(
                            "validation_error", {"type": "request_body", "error": error}
                        )
                        response = JSONResponse(
                            status_code=400, content={"error": error}
                        )
                        await response(scope, receive, send)
                        return
                except Exception as e:
                    log_event(
                        "validation_error", {"type": "json_parse", "error": str(e)}
                    )
                    response = JSONResponse(
                        status_code=400,
                        content={"error": "Invalid JSON in request body"},
                    )
                    await response(scope, receive, send)
                    return

            # Process request
            await call_next(request)

        except Exception as e:
            log_event("validation_error", {"type": "unexpected", "error": str(e)})
            response = JSONResponse(
                status_code=500,
                content={"error": "Internal server error during validation"},
            )
            await response(scope, receive, send)


def setup_validation(
    app,
    max_url_length: int = 2048,
    allowed_schemes: List[str] = None,
    blocked_domains: List[str] = None,
    max_content_length: int = 10 * 1024 * 1024,
):
    """
    Set up request validation for FastAPI application

    Args:
        app: FastAPI application
        max_url_length: Maximum allowed URL length
        allowed_schemes: List of allowed URL schemes
        blocked_domains: List of blocked domains
        max_content_length: Maximum allowed content length
    """
    validator = RequestValidator(
        max_url_length=max_url_length,
        allowed_schemes=allowed_schemes,
        blocked_domains=blocked_domains,
        max_content_length=max_content_length,
    )

    app.add_middleware(ValidationMiddleware, validator=validator)
