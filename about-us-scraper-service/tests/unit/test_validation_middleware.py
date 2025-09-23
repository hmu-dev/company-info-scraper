import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
from api.middleware.validation import RequestValidator, ValidationMiddleware, setup_validation
import json

@pytest.fixture
def validator():
    """Create a RequestValidator instance with test settings."""
    return RequestValidator(
        max_url_length=50,
        allowed_schemes=['http', 'https'],
        blocked_domains=['blocked.com'],
        max_content_length=1000
    )

@pytest.fixture
def app():
    """Create a FastAPI app with validation middleware for testing."""
    app = FastAPI()
    
    @app.post("/test")
    async def test_endpoint():
        return {"message": "success"}
    
    @app.get("/health")
    async def health_endpoint():
        return {"status": "ok"}
    
    validator = RequestValidator(
        max_url_length=50,
        allowed_schemes=['http', 'https'],
        blocked_domains=['blocked.com'],
        max_content_length=1000
    )
    
    app.add_middleware(
        ValidationMiddleware,
        validator=validator,
        exclude_paths=["/health"]
    )
    
    return app

@pytest.fixture
def client(app):
    """Create a TestClient for the FastAPI app."""
    return TestClient(app)

def test_validate_url_success(validator):
    """Test successful URL validation."""
    url = "https://example.com"
    error = validator.validate_url(url)
    assert error is None

def test_validate_url_too_long(validator):
    """Test URL length validation."""
    url = "https://" + "a" * 50 + ".com"
    error = validator.validate_url(url)
    assert error == "URL length exceeds maximum of 50 characters"

def test_validate_url_invalid_format(validator):
    """Test invalid URL format validation."""
    url = "not-a-url"
    error = validator.validate_url(url)
    assert error == "Invalid URL format"

def test_validate_url_invalid_scheme(validator):
    """Test URL scheme validation."""
    url = "ftp://example.com"
    error = validator.validate_url(url)
    assert error == "URL scheme must be one of: http, https"

def test_validate_url_blocked_domain(validator):
    """Test blocked domain validation."""
    url = "https://blocked.com"
    error = validator.validate_url(url)
    assert error == "Access to this domain is blocked"

def test_validate_url_invalid_characters(validator):
    """Test URL character validation."""
    url = "https://example.com/<script>"
    error = validator.validate_url(url)
    assert error == "URL contains invalid characters"

def test_sanitize_string(validator):
    """Test string sanitization."""
    input_str = "Hello  <script>alert('xss')</script>  World\n\t"
    sanitized = validator.sanitize_string(input_str)
    assert sanitized == "Hello &lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt; World"
    assert "<" not in sanitized
    assert ">" not in sanitized
    assert "\n" not in sanitized
    assert "\t" not in sanitized

def test_validate_api_key_success(validator):
    """Test successful API key validation."""
    api_key = "sk-" + "a" * 32
    error = validator.validate_api_key(api_key)
    assert error is None

def test_validate_api_key_too_short(validator):
    """Test API key length validation."""
    api_key = "sk-" + "a" * 10
    error = validator.validate_api_key(api_key)
    assert error == "Invalid API key format"  # Format check fails first

def test_validate_api_key_invalid_format(validator):
    """Test API key format validation."""
    api_key = "invalid-key"
    error = validator.validate_api_key(api_key)
    assert error == "Invalid API key format"

def test_validate_api_key_none(validator):
    """Test None API key validation."""
    error = validator.validate_api_key(None)
    assert error is None

def test_validate_content_length_success(validator):
    """Test successful content length validation."""
    error = validator.validate_content_length(500)
    assert error is None

def test_validate_content_length_too_large(validator):
    """Test content length limit validation."""
    error = validator.validate_content_length(2000)
    assert error == "Content length exceeds maximum of 1000 bytes"

def test_validate_request_body_success(validator):
    """Test successful request body validation."""
    body = {
        "url": "https://example.com",
        "model": "gpt-3.5-turbo",
        "openai_api_key": "sk-" + "a" * 32
    }
    error = validator.validate_request_body(body)
    assert error is None

def test_validate_request_body_missing_url(validator):
    """Test missing URL in request body."""
    body = {"model": "gpt-3.5-turbo"}
    error = validator.validate_request_body(body)
    assert error == "Missing required fields: url"

def test_validate_request_body_invalid_url(validator):
    """Test invalid URL in request body."""
    body = {"url": "not-a-url"}
    error = validator.validate_request_body(body)
    assert error == "Invalid URL format"

def test_validate_request_body_invalid_api_key(validator):
    """Test invalid API key in request body."""
    body = {
        "url": "https://example.com",
        "openai_api_key": "invalid-key"
    }
    error = validator.validate_request_body(body)
    assert error == "Invalid API key format"

def test_validate_request_body_invalid_model(validator):
    """Test invalid model name in request body."""
    body = {
        "url": "https://example.com",
        "model": "invalid!model"
    }
    error = validator.validate_request_body(body)
    assert error == "Invalid model name format"

def test_middleware_excluded_path(client):
    """Test that excluded paths bypass validation."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_middleware_content_length_too_large(client):
    """Test content length validation in middleware."""
    headers = {"content-length": "2000"}
    response = client.post("/test", headers=headers, json={"url": "https://example.com"})
    assert response.status_code == 413
    assert "error" in response.json()
    assert "Content length exceeds maximum" in response.json()["error"]

def test_middleware_invalid_json(client):
    """Test invalid JSON handling in middleware."""
    response = client.post(
        "/test",
        headers={"content-type": "application/json"},
        content="invalid json"
    )
    assert response.status_code == 400
    assert response.json() == {"error": "Invalid JSON in request body"}

def test_middleware_invalid_request_body(client):
    """Test request body validation in middleware."""
    response = client.post("/test", json={"invalid": "body"})
    assert response.status_code == 400
    assert "error" in response.json()
    assert "Missing required fields: url" in response.json()["error"]

def test_middleware_success(client):
    """Test successful request validation."""
    response = client.post(
        "/test",
        json={
            "url": "https://example.com",
            "model": "gpt-3.5-turbo",
            "openai_api_key": "sk-" + "a" * 32
        }
    )
    assert response.status_code == 200
    assert response.json() == {"message": "success"}

def test_setup_validation():
    """Test validation middleware setup function."""
    app = FastAPI()
    
    @app.post("/test")
    async def test_endpoint():
        return {"message": "success"}
    
    @app.get("/health")
    async def health_endpoint():
        return {"status": "ok"}
    
    setup_validation(
        app,
        max_url_length=100,
        allowed_schemes=['http', 'https'],
        blocked_domains=['blocked.com'],
        max_content_length=2000,
        exclude_paths=["/health"]
    )
    
    # Create a test client to verify the middleware is working
    client = TestClient(app)
    
    # Test that validation is working
    response = client.post(
        "/test",
        json={"url": "https://blocked.com"}
    )
    assert response.status_code == 400
    assert response.json()["error"] == "Access to this domain is blocked"
    
    # Test that excluded paths bypass validation
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    
    # Test content length validation
    response = client.post(
        "/test",
        headers={"content-length": "3000"},
        json={"url": "https://example.com"}
    )
    assert response.status_code == 413
    assert "Content length exceeds maximum" in response.json()["error"]

@pytest.mark.asyncio
async def test_middleware_unexpected_error():
    """Test handling of unexpected errors in middleware."""
    # Create a mock app that raises an exception
    async def mock_app(scope, receive, send):
        raise Exception("Unexpected error")
    
    # Create the middleware
    validator = RequestValidator()
    middleware = ValidationMiddleware(mock_app, validator)
    
    # Create mock scope and receive function
    scope = {"type": "http", "method": "POST", "path": "/test"}
    receive = AsyncMock()
    send = AsyncMock()
    
    # Call middleware
    await middleware(scope, receive, send)
    
    # Check that error response was sent
    assert send.call_count > 0
    call_args = send.call_args_list
    
    # Find the response body
    response_body = None
    for call in call_args:
        message = call[0][0]
        if message["type"] == "http.response.body":
            response_body = json.loads(message["body"].decode())
            break
    
    assert response_body == {"error": "Internal server error during validation"}
