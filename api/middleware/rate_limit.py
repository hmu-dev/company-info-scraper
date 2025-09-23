import asyncio
import time
from typing import Dict, Optional, Tuple

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from ..utils.logging import log_event


class RateLimiter:
    def __init__(
        self, requests_per_minute: int = 60, burst_limit: int = 10, key_func=None
    ):
        """
        Initialize rate limiter with token bucket algorithm

        Args:
            requests_per_minute: Number of requests allowed per minute
            burst_limit: Maximum number of requests allowed in burst
            key_func: Function to extract key from request (e.g., IP, API key)
        """
        self.rate = requests_per_minute / 60.0  # tokens per second
        self.burst_limit = burst_limit
        self.key_func = key_func or (lambda r: r.client.host)
        self.tokens: Dict[str, Tuple[float, float]] = {}  # key -> (tokens, last_update)
        self._lock = asyncio.Lock()

    async def _get_tokens(self, key: str) -> Tuple[float, float]:
        """Get current token count and last update time for key"""
        now = time.time()
        if key not in self.tokens:
            return self.burst_limit, now

        tokens, last_update = self.tokens[key]
        time_passed = now - last_update
        new_tokens = min(self.burst_limit, tokens + time_passed * self.rate)
        return new_tokens, now

    async def _update_tokens(self, key: str, tokens: float, last_update: float):
        """Update token count and last update time for key"""
        self.tokens[key] = (tokens, last_update)

    async def is_allowed(self, request: Request) -> bool:
        """Check if request is allowed under rate limit"""
        key = self.key_func(request)

        async with self._lock:
            tokens, now = await self._get_tokens(key)

            if tokens >= 1:
                await self._update_tokens(key, tokens - 1, now)
                return True

            return False

    async def get_retry_after(self, request: Request) -> float:
        """Get seconds until next request is allowed"""
        key = self.key_func(request)
        tokens, _ = await self._get_tokens(key)
        if tokens >= 1:
            return 0

        return (1 - tokens) / self.rate


class RateLimitMiddleware:
    def __init__(self, app, limiter: RateLimiter, exclude_paths: Optional[list] = None):
        """
        Initialize rate limit middleware

        Args:
            app: FastAPI application
            limiter: Rate limiter instance
            exclude_paths: List of paths to exclude from rate limiting
        """
        self.app = app
        self.limiter = limiter
        self.exclude_paths = exclude_paths or []

    async def __call__(self, scope, receive, send):
        """Process request with rate limiting"""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        from fastapi import Request

        request = Request(scope, receive)

        async def call_next(request):
            async def send_wrapper(message):
                await send(message)

            return await self.app(scope, receive, send_wrapper)

        # Skip rate limiting for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            await call_next(request)
            return

        # Check rate limit
        if not await self.limiter.is_allowed(request):
            retry_after = await self.limiter.get_retry_after(request)

            # Log rate limit exceeded
            log_event(
                "rate_limit_exceeded",
                {
                    "path": request.url.path,
                    "method": request.method,
                    "client": request.client.host,
                    "retry_after": retry_after,
                },
            )

            from fastapi.responses import JSONResponse

            response = JSONResponse(
                status_code=429,
                content={"error": "Too Many Requests", "retry_after": retry_after},
                headers={"Retry-After": str(int(retry_after))},
            )
            await response(scope, receive, send)
            return

        # Process request
        await call_next(request)


def create_rate_limiter(
    requests_per_minute: int = 60, burst_limit: int = 10, key_func=None
) -> RateLimiter:
    """Create a rate limiter instance with default settings"""
    return RateLimiter(
        requests_per_minute=requests_per_minute,
        burst_limit=burst_limit,
        key_func=key_func,
    )


def setup_rate_limiting(
    app,
    requests_per_minute: int = 60,
    burst_limit: int = 10,
    exclude_paths: Optional[list] = None,
    key_func=None,
):
    """
    Set up rate limiting for FastAPI application

    Args:
        app: FastAPI application
        requests_per_minute: Number of requests allowed per minute
        burst_limit: Maximum number of requests allowed in burst
        exclude_paths: List of paths to exclude from rate limiting
        key_func: Function to extract key from request (e.g., IP, API key)
    """
    limiter = create_rate_limiter(
        requests_per_minute=requests_per_minute,
        burst_limit=burst_limit,
        key_func=key_func,
    )

    app.add_middleware(
        RateLimitMiddleware, limiter=limiter, exclude_paths=exclude_paths
    )
