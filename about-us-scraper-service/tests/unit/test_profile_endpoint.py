"""Unit tests for profile endpoint."""
import pytest
from fastapi import Response
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
from api.endpoints.profile import router
from api.models import ScrapeRequest, ProfileResponse
from api.services.llm import LLMService, LLMError
from pydantic import HttpUrl

@pytest.fixture
def client():
    """Create FastAPI test client."""
    from fastapi import FastAPI
    from api.middleware.rate_limit import RateLimiter, RateLimitMiddleware
    app = FastAPI()
    limiter = RateLimiter(
        requests_per_minute=5,
        burst_limit=5,
        key_func=lambda r: r.client.host
    )
    app.add_middleware(
        RateLimitMiddleware,
        limiter=limiter
    )
    app.include_router(router)
    return TestClient(app)

@pytest.fixture
def mock_llm():
    """Mock LLMService."""
    with patch("api.endpoints.profile.LLMService") as mock:
        llm_instance = Mock(spec=LLMService)
        llm_instance.extract_content = AsyncMock(return_value={
            "about_us": "Example Company is a leading provider...",
            "our_culture": "We believe in innovation and collaboration...",
            "our_team": "Led by CEO Jane Smith...",
            "noteworthy_and_differentiated": "Award-winning technology...",
            "locations": "Headquarters in San Francisco, CA"
        })
        mock.return_value = llm_instance
        yield llm_instance

def test_scrape_profile_success(client, mock_llm):
    """Test successful profile extraction."""
    # Execute
    response = client.post(
        "/profile",
        json={
            "url": "https://example.com",
            "model": "anthropic.claude-instant-v1",
            "openai_api_key": "test-key"
        }
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "duration" in data
    assert data["duration"] >= 0
    assert "data" in data
    assert data["data"]["about_us"] == "Example Company is a leading provider..."
    assert data["data"]["our_culture"] == "We believe in innovation and collaboration..."
    assert data["data"]["our_team"] == "Led by CEO Jane Smith..."
    assert data["data"]["noteworthy_and_differentiated"] == "Award-winning technology..."
    assert data["data"]["locations"] == "Headquarters in San Francisco, CA"

def test_scrape_profile_llm_error(client, mock_llm):
    """Test LLM error handling."""
    # Setup
    mock_llm.extract_content = AsyncMock(
        side_effect=LLMError("Failed to process content")
    )

    # Execute
    response = client.post(
        "/profile",
        json={
            "url": "https://example.com",
            "model": "anthropic.claude-instant-v1",
            "openai_api_key": "test-key"
        }
    )

    # Assert
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert data["detail"]["error"] == "Failed to process content"
    assert data["detail"]["error_type"] == "LLMError"

def test_scrape_profile_invalid_request(client):
    """Test invalid URL handling."""
    # Execute
    response = client.post(
        "/profile",
        json={
            "url": "not-a-url",
            "model": "anthropic.claude-instant-v1",
            "openai_api_key": "test-key"
        }
    )

    # Assert
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert len(data["detail"]) == 1
    error = data["detail"][0]
    assert error["type"] == "url_parsing"
    assert error["loc"] == ["body", "url"]
    assert "relative URL without a base" in error["msg"]

def test_scrape_profile_missing_api_key(client, mock_llm):
    """Test missing API key handling."""
    # Setup
    mock_llm.extract_content = AsyncMock(return_value={
        "about_us": "Example Company is a leading provider...",
        "our_culture": "We believe in innovation and collaboration...",
        "our_team": "Led by CEO Jane Smith...",
        "noteworthy_and_differentiated": "Award-winning technology...",
        "locations": "Headquarters in San Francisco, CA"
    })

    # Execute
    response = client.post(
        "/profile",
        json={
            "url": "https://example.com",
            "model": "anthropic.claude-instant-v1"
        }
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "duration" in data
    assert data["duration"] >= 0
    assert "data" in data
    assert data["data"]["about_us"] == "Example Company is a leading provider..."
    assert data["data"]["our_culture"] == "We believe in innovation and collaboration..."
    assert data["data"]["our_team"] == "Led by CEO Jane Smith..."
    assert data["data"]["noteworthy_and_differentiated"] == "Award-winning technology..."
    assert data["data"]["locations"] == "Headquarters in San Francisco, CA"
    assert "token_usage" in data
    assert data["token_usage"]["prompt_tokens"] == 0
    assert data["token_usage"]["completion_tokens"] == 0

def test_scrape_profile_invalid_model(client):
    """Test invalid model handling."""
    # Execute
    response = client.post(
        "/profile",
        json={
            "url": "https://example.com",
            "model": "invalid-model",
            "openai_api_key": "test-key"
        }
    )

    # Assert
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data
    assert len(data["detail"]) == 1
    error = data["detail"][0]
    assert error["type"] == "string_pattern_mismatch"
    assert error["loc"] == ["body", "model"]
    assert "String should match pattern" in error["msg"]

def test_scrape_profile_rate_limit(client, mock_llm):
    """Test rate limit response headers."""
    # Execute first request
    response = client.post(
        "/profile",
        json={
            "url": "https://example.com",
            "model": "anthropic.claude-instant-v1",
            "openai_api_key": "test-key"
        }
    )

    # Assert rate limit headers
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert "X-RateLimit-Reset" in response.headers

    # Execute many requests to trigger rate limit
    for _ in range(10):
        response = client.post(
            "/profile",
            json={
                "url": "https://example.com",
                "model": "anthropic.claude-instant-v1",
                "openai_api_key": "test-key"
            }
        )

    # Assert rate limit response
    assert response.status_code == 429
    assert "Retry-After" in response.headers
    data = response.json()
    assert "detail" in data
    assert data["detail"]["error"] == "Too Many Requests"
