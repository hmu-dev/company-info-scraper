"""
Basic import tests to ensure the API can be imported without errors.
"""

import pytest


def test_api_imports():
    """Test that the main API modules can be imported."""
    try:
        from api import main, models
        from api.endpoints import media, profile
        from api.middleware import compression, rate_limit, tracing, validation
        from api.services import llm
        from api.services import media as media_service
        from api.utils import cache, logging, pagination, retry, storage, versioning
    except ImportError as e:
        pytest.fail(f"Failed to import API modules: {e}")


def test_fastapi_app_creation():
    """Test that the FastAPI app can be created."""
    try:
        from api.main import app

        assert app is not None
        assert app.title == "AI Web Scraper API"
    except Exception as e:
        pytest.fail(f"Failed to create FastAPI app: {e}")


def test_split_api_imports():
    """Test that the split API modules can be imported."""
    try:
        from about_us_scraper_service.api.main_split import app
        from about_us_scraper_service.api.lambda_handler_split import lambda_handler
        
        assert app is not None
        assert app.title == "AI Web Scraper API - Split Approach"
        assert callable(lambda_handler)
    except ImportError as e:
        pytest.fail(f"Failed to import split API modules: {e}")


def test_health_endpoint_exists():
    """Test that the health endpoint is registered."""
    from api.main import app

    # Check if health endpoint exists in the app routes
    routes = [route.path for route in app.routes]
    assert "/health" in routes


@pytest.mark.asyncio
async def test_health_endpoint_response():
    """Test that the health endpoint returns a valid response."""
    from fastapi.testclient import TestClient

    from api.main import app

    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
