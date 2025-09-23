import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
from api.middleware.rate_limit import (
    RateLimiter,
    RateLimitMiddleware,
    create_rate_limiter,
    setup_rate_limiting
)
import time
import asyncio

@pytest.fixture
def app():
    """Create a FastAPI app with rate limit middleware for testing."""
    app = FastAPI()
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "success"}
    
    @app.get("/health")
    async def health_endpoint():
        return {"status": "ok"}
    
    limiter = RateLimiter(
        requests_per_minute=5,
        burst_limit=5,
        key_func=lambda r: r.client.host
    )
    
    app.add_middleware(
        RateLimitMiddleware,
        limiter=limiter,
        exclude_paths=["/health"]
    )
    
    return app

@pytest.fixture
def client(app):
    """Create a TestClient for the FastAPI app."""
    return TestClient(app)

@pytest.fixture
def limiter():
    """Create a RateLimiter instance for testing."""
    return RateLimiter(
        requests_per_minute=5,
        burst_limit=5,
        key_func=lambda r: r.client.host
    )

def test_rate_limiter_init():
    """Test rate limiter initialization."""
    limiter = RateLimiter(
        requests_per_minute=60,
        burst_limit=10,
        key_func=lambda r: r.client.host
    )
    assert limiter.rate == 1.0  # 60 requests per minute = 1 per second
    assert limiter.burst_limit == 10
    assert callable(limiter.key_func)
    assert isinstance(limiter._lock, asyncio.Lock)

@pytest.mark.asyncio
async def test_get_tokens_new_key():
    """Test getting tokens for a new key."""
    limiter = RateLimiter(requests_per_minute=60, burst_limit=10)
    tokens, now = await limiter._get_tokens("test-key")
    assert tokens == 10  # Should get burst limit for new key
    assert isinstance(now, float)
    assert now <= time.time()

@pytest.mark.asyncio
async def test_get_tokens_existing_key():
    """Test getting tokens for an existing key."""
    limiter = RateLimiter(requests_per_minute=60, burst_limit=10)
    
    # Set initial tokens
    await limiter._update_tokens("test-key", 5.0, time.time() - 1)  # 1 second ago
    
    tokens, now = await limiter._get_tokens("test-key")
    assert 5.0 < tokens < 6.1  # Should have gained ~1 token
    assert isinstance(now, float)
    assert now <= time.time()

@pytest.mark.asyncio
async def test_get_tokens_max_burst():
    """Test that tokens don't exceed burst limit."""
    limiter = RateLimiter(requests_per_minute=60, burst_limit=10)
    
    # Set initial tokens and last update far in the past
    await limiter._update_tokens("test-key", 5.0, time.time() - 100)
    
    tokens, now = await limiter._get_tokens("test-key")
    assert tokens == 10  # Should be capped at burst limit
    assert isinstance(now, float)
    assert now <= time.time()

@pytest.mark.asyncio
async def test_is_allowed_success():
    """Test successful rate limit check."""
    limiter = RateLimiter(requests_per_minute=60, burst_limit=10)
    request = Mock(spec=Request)
    request.client.host = "127.0.0.1"
    
    allowed = await limiter.is_allowed(request)
    assert allowed is True
    
    tokens, _ = await limiter._get_tokens("127.0.0.1")
    assert tokens == pytest.approx(9.0, rel=1e-3)  # Should have used one token

@pytest.mark.asyncio
async def test_is_allowed_no_tokens():
    """Test rate limit check with no tokens."""
    limiter = RateLimiter(requests_per_minute=60, burst_limit=10)
    request = Mock(spec=Request)
    request.client.host = "127.0.0.1"
    
    # Use up all tokens
    await limiter._update_tokens("127.0.0.1", 0.0, time.time())
    
    allowed = await limiter.is_allowed(request)
    assert allowed is False

@pytest.mark.asyncio
async def test_get_retry_after():
    """Test getting retry after time."""
    limiter = RateLimiter(requests_per_minute=60, burst_limit=10)
    request = Mock(spec=Request)
    request.client.host = "127.0.0.1"
    
    # Set 0.5 tokens (need 0.5 more)
    await limiter._update_tokens("127.0.0.1", 0.5, time.time())
    
    retry_after = await limiter.get_retry_after(request)
    assert retry_after == pytest.approx(0.5, rel=0.1)  # Should need ~0.5 seconds

def test_middleware_success(client):
    """Test successful request with rate limiting."""
    response = client.get("/test")
    assert response.status_code == 200
    assert response.json() == {"message": "success"}
    
    # Check rate limit headers
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers
    
    assert int(response.headers["X-RateLimit-Limit"]) == 5
    assert 0 <= int(response.headers["X-RateLimit-Remaining"]) <= 5
    assert int(response.headers["X-RateLimit-Reset"]) > time.time()

def test_middleware_excluded_path(client):
    """Test that excluded paths bypass rate limiting."""
    # Make requests to use up the rate limit
    for _ in range(10):
        client.get("/test")
    
    # Health endpoint should still work
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert "X-RateLimit-Limit" not in response.headers

def test_middleware_rate_limit_exceeded(client):
    """Test rate limit exceeded response."""
    # Make requests to use up the rate limit
    for _ in range(5):
        response = client.get("/test")
        assert response.status_code == 200
    
    # Next request should be rate limited
    response = client.get("/test")
    assert response.status_code == 429
    assert "error" in response.json()["detail"]
    assert response.json()["detail"]["error"] == "Too Many Requests"
    assert response.json()["detail"]["error_type"] == "RateLimitExceeded"
    assert "retry_after" in response.json()["detail"]
    assert "Retry-After" in response.headers

def test_create_rate_limiter():
    """Test rate limiter creation helper."""
    limiter = create_rate_limiter(
        requests_per_minute=30,
        burst_limit=5,
        key_func=lambda r: r.client.host
    )
    assert isinstance(limiter, RateLimiter)
    assert limiter.rate == 0.5  # 30 requests per minute = 0.5 per second
    assert limiter.burst_limit == 5
    assert callable(limiter.key_func)

def test_setup_rate_limiting():
    """Test rate limiting setup helper."""
    app = FastAPI()
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "success"}
    
    @app.get("/health")
    async def health_endpoint():
        return {"status": "ok"}
    
    setup_rate_limiting(
        app,
        requests_per_minute=30,
        burst_limit=5,
        exclude_paths=["/health"],
        key_func=lambda r: r.client.host
    )
    
    # Check that middleware was added
    middleware = next(
        m for m in app.user_middleware
        if isinstance(m.cls, type) and m.cls.__name__ == "RateLimitMiddleware"
    )
    assert middleware is not None
    
    # Create a test client to verify the configuration
    client = TestClient(app)
    
    # Make requests to verify rate limit
    for _ in range(5):
        response = client.get("/test")
        assert response.status_code == 200
    
    # Next request should be rate limited
    response = client.get("/test")
    assert response.status_code == 429
    
    # Health endpoint should bypass rate limit
    response = client.get("/health")
    assert response.status_code == 200

@pytest.mark.asyncio
async def test_middleware_non_http():
    """Test handling of non-HTTP requests."""
    middleware = RateLimitMiddleware(AsyncMock(), RateLimiter())
    scope = {
        "type": "websocket",
        "headers": [],
        "client": ("127.0.0.1", 1234),
        "query_string": b"",
        "scheme": "ws",
        "server": ("testserver", 80)
    }
    receive = AsyncMock()
    send = AsyncMock()
    
    await middleware(scope, receive, send)
    middleware.app.assert_called_once_with(scope, receive, send)

def test_rate_limit_custom_key_func():
    """Test rate limiter with custom key function."""
    def custom_key_func(request):
        return request.headers.get("X-API-Key", "default")
    
    limiter = RateLimiter(
        requests_per_minute=60,
        burst_limit=10,
        key_func=custom_key_func
    )
    
    request = Mock(spec=Request)
    request.headers = {"X-API-Key": "test-key"}
    
    key = limiter.key_func(request)
    assert key == "test-key"

def test_rate_limit_concurrent_requests(client):
    """Test rate limiting with concurrent requests."""
    # Make concurrent requests
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(client.get, "/test")
            for _ in range(10)
        ]
        responses = [f.result() for f in futures]
    
    # Should have 5 successful requests and 5 rate limited
    success_count = sum(1 for r in responses if r.status_code == 200)
    rate_limited_count = sum(1 for r in responses if r.status_code == 429)
    
    assert success_count == 5
    assert rate_limited_count == 5
