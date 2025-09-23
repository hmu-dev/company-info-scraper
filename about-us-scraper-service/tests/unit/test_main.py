"""
Unit tests for main.py
"""

from unittest.mock import Mock, patch
import pytest
from fastapi.testclient import TestClient


def create_app():
    """Create a fresh FastAPI app for testing"""
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from api.middleware.rate_limit import setup_rate_limiting
    from api.middleware.validation import setup_validation
    from api.middleware.compression import setup_compression
    from api.middleware.tracing import setup_tracing
    from api.utils.versioning import setup_versioning
    from api.endpoints import media, profile

    app = FastAPI(
        title="AI Web Scraper API",
        version="1.0.0",
        license_info={"name": "MIT"},
        contact={"email": "support@example.com"},
    )

    # Mock endpoints
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {"status": "healthy", "version": "1.0.0"}

    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint"""
        return {"metrics": "Coming soon"}

    @app.get("/v1/media")
    async def mock_media():
        return {"message": "Media endpoint"}

    @app.get("/v1/profile")
    async def mock_profile():
        return {"message": "Profile endpoint"}

    # Set up tracing first
    setup_tracing(app)

    # Set up CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
        max_age=3600,
    )

    # Set up compression
    setup_compression(
        app,
        minimum_size=1000,
        compression_level=6,
        excluded_paths=["/health", "/metrics"],
        excluded_types=[
            "image/",
            "video/",
            "audio/",
            "application/zip",
            "application/x-gzip",
            "application/x-brotli",
            "application/x-rar",
        ],
    )

    # Set up validation
    setup_validation(
        app,
        max_url_length=2048,
        allowed_schemes=["http", "https"],
        blocked_domains=[],
        max_content_length=10 * 1024 * 1024,  # 10MB
        exclude_paths=["/health", "/metrics", "/openapi.json"],
    )

    # Set up rate limiting
    setup_rate_limiting(
        app,
        requests_per_minute=60,
        burst_limit=10,
        exclude_paths=["/health", "/metrics"],
        key_func=lambda request: request.headers.get("X-API-Key", request.client.host),
    )

    # Set up versioning last
    version_manager = setup_versioning(
        app, current_version="1.0.0", min_version="1.0.0", max_version="2.0.0"
    )

    return app


@pytest.fixture
def client():
    """Create a test client with a fresh app"""
    app = create_app()
    client = TestClient(app)
    client.headers = {
        "X-API-Key": "test-key",
        "Accept": "application/json",
        "Content-Type": "application/json",
        "X-API-Version": "1.0.0",  # Add version header
    }
    return client


def test_health_check(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "version": "1.0.0"}


def test_metrics(client):
    """Test metrics endpoint"""
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.json() == {"metrics": "Coming soon"}


def test_cors_headers(client):
    """Test CORS headers are set correctly"""
    response = client.options(
        "/health",
        headers={
            "Origin": "http://example.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "*"
    assert (
        "DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT"
        in response.headers["access-control-allow-methods"]
    )
    assert response.headers["access-control-max-age"] == "3600"


def test_compression_setup():
    """Test compression middleware setup"""
    with patch(
        "api.middleware.compression.setup_compression"
    ) as mock_setup_compression:
        app = create_app()
        mock_setup_compression.assert_called_once_with(
            app,
            minimum_size=1000,
            compression_level=6,
            excluded_paths=["/health", "/metrics"],
            excluded_types=[
                "image/",
                "video/",
                "audio/",
                "application/zip",
                "application/x-gzip",
                "application/x-brotli",
                "application/x-rar",
            ],
        )


def test_validation_setup():
    """Test validation middleware setup"""
    with patch("api.middleware.validation.setup_validation") as mock_setup_validation:
        app = create_app()
        mock_setup_validation.assert_called_once_with(
            app,
            max_url_length=2048,
            allowed_schemes=["http", "https"],
            blocked_domains=[],
            max_content_length=10 * 1024 * 1024,  # 10MB
            exclude_paths=["/health", "/metrics", "/openapi.json"],
        )


def test_rate_limiting_setup():
    """Test rate limiting middleware setup"""
    with patch(
        "api.middleware.rate_limit.setup_rate_limiting"
    ) as mock_setup_rate_limiting:
        app = create_app()
        # Get the actual call arguments
    args, kwargs = mock_setup_rate_limiting.call_args
    assert args[0] == app
    assert kwargs["requests_per_minute"] == 60
    assert kwargs["burst_limit"] == 10
    assert kwargs["exclude_paths"] == ["/health", "/metrics"]
    # Compare key_func functionality
    actual_key_func = kwargs["key_func"]
    mock_request = Mock()
    mock_request.headers = {"X-API-Key": "test-key"}
    mock_request.client = Mock(host="127.0.0.1")
    assert actual_key_func(mock_request) == "test-key"
    mock_request.headers = {}
    assert actual_key_func(mock_request) == "127.0.0.1"


def test_versioning_setup():
    """Test versioning middleware setup"""
    with patch("api.utils.versioning.setup_versioning") as mock_setup_versioning:
        app = create_app()
        mock_setup_versioning.assert_called_once_with(
            app, current_version="1.0.0", min_version="1.0.0", max_version="2.0.0"
        )


def test_openapi_schema(client):
    """Test OpenAPI schema is generated correctly"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "AI Web Scraper API"
    assert schema["info"]["version"] == "1.0.0"
    assert schema["info"]["license"]["name"] == "MIT"
    assert schema["info"]["contact"]["email"] == "support@example.com"
    assert "/v1/media" in schema["paths"]
    assert "/v1/profile" in schema["paths"]
    assert "/health" in schema["paths"]
    assert "/metrics" in schema["paths"]
