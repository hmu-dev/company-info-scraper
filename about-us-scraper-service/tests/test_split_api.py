"""
Tests for the split API endpoints in the SAM service.
"""

import base64
import json
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient


class TestSAMSplitAPI:
    """Test suite for the SAM service split API endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client for the SAM split API."""
        from main_split import app

        return TestClient(app)

    def test_health_endpoint(self, client):
        """Test the health endpoint returns correct split API info."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "3.0.0"
        assert data["approach"] == "split"

    @patch("main_split.get_page_content")
    @patch("main_split.extract_company_info_programmatic")
    @patch("main_split.find_about_pages")
    def test_scrape_text_endpoint(
        self, mock_find_about, mock_extract_company, mock_get_content, client
    ):
        """Test the /scrape/text endpoint."""
        # Mock the dependencies
        mock_soup = Mock()
        mock_get_content.return_value = (mock_soup, "<html>test</html>", 200)

        mock_company_data = {
            "title": "Test Company",
            "description": "A test company",
            "content": "Test content",
            "company_info": {
                "founded": "2020",
                "employees": "10",
                "location": "Test City",
                "mission": "Test mission",
                "confidence": "high",
            },
            "url": "https://test.com",
        }
        mock_extract_company.return_value = mock_company_data

        mock_about_pages = [
            {
                "url": "https://test.com/about",
                "title": "About Us",
                "relevance_score": 0.9,
            }
        ]
        mock_find_about.return_value = mock_about_pages

        # Test the endpoint
        response = client.get("/scrape/text?url=test.com")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["success"] is True
        assert data["url"] == "https://test.com"
        assert data["title"] == "Test Company"
        assert data["description"] == "A test company"
        assert data["company_info"]["founded"] == "2020"
        assert data["about_pages_found"] == 1
        assert data["approach_used"] == "programmatic_only"
        assert "processing_time_seconds" in data

    @patch("main_split.get_page_content")
    @patch("main_split.extract_media_assets")
    def test_scrape_media_endpoint_pagination(
        self, mock_extract_media, mock_get_content, client
    ):
        """Test the /scrape/media endpoint with pagination."""
        # Mock the dependencies
        mock_soup = Mock()
        mock_get_content.return_value = (mock_soup, "<html>test</html>", 200)

        mock_media_data = {
            "media_assets": [
                {
                    "id": "test123",
                    "url": "https://test.com/logo.png",
                    "type": "image",
                    "alt": "Company Logo",
                    "priority": 100,
                    "context": "Company Logo",
                }
            ],
            "media_summary": {
                "total_assets": 5,
                "images_count": 5,
                "videos_count": 0,
                "documents_count": 0,
                "icons_count": 0,
                "current_page_count": 1,
                "has_more": True,
            },
            "pagination": {
                "next_cursor": base64.b64encode("media:1".encode()).decode(),
                "has_more": True,
                "total_count": 5,
                "current_page_start": 0,
                "current_page_end": 1,
            },
        }
        mock_extract_media.return_value = mock_media_data

        # Test the endpoint
        response = client.get("/scrape/media?url=test.com&limit=1")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["success"] is True
        assert data["url"] == "https://test.com"
        assert len(data["media_assets"]) == 1
        assert data["media_assets"][0]["type"] == "image"
        assert data["media_summary"]["total_assets"] == 5
        assert data["pagination"]["has_more"] is True
        assert "next_cursor" in data["pagination"]
        assert data["approach_used"] == "programmatic_only"

    def test_lambda_handler_integration(self):
        """Test the lambda handler with a valid API Gateway event."""
        from lambda_handler_split import lambda_handler

        # Create a valid API Gateway event
        event = {
            "version": "2.0",
            "routeKey": "GET /health",
            "rawPath": "/health",
            "rawQueryString": "",
            "headers": {"accept": "*/*", "user-agent": "test-agent"},
            "requestContext": {
                "accountId": "123456789012",
                "apiId": "test-api",
                "domainName": "test.execute-api.us-east-1.amazonaws.com",
                "http": {
                    "method": "GET",
                    "path": "/health",
                    "protocol": "HTTP/1.1",
                    "sourceIp": "127.0.0.1",
                    "userAgent": "test-agent",
                },
                "requestId": "test-request-id",
                "routeKey": "GET /health",
                "stage": "test",
                "time": "09/Apr/2015:12:34:56 +0000",
                "timeEpoch": 1428582896000,
            },
            "body": None,
            "isBase64Encoded": False,
        }

        context = Mock()

        # Test the lambda handler
        response = lambda_handler(event, context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["status"] == "healthy"
        assert body["version"] == "3.0.0"
        assert body["approach"] == "split"

    def test_cursor_pagination_logic(self):
        """Test cursor pagination encoding and decoding."""
        from unittest.mock import Mock

        from main_split import extract_media_assets

        # Mock soup with no media
        mock_soup = Mock()
        mock_soup.find_all.return_value = []

        # Test pagination logic
        result = extract_media_assets(mock_soup, "https://test.com", None, 10)

        # Verify pagination structure
        assert "pagination" in result
        assert "next_cursor" in result["pagination"]
        assert "has_more" in result["pagination"]
        assert "total_count" in result["pagination"]
        assert "current_page_start" in result["pagination"]
        assert "current_page_end" in result["pagination"]

        # Test cursor decoding
        if result["pagination"]["has_more"]:
            cursor = result["pagination"]["next_cursor"]
            decoded = base64.b64decode(cursor).decode()
            assert decoded.startswith("media:")

            # Test using the cursor
            result2 = extract_media_assets(mock_soup, "https://test.com", cursor, 10)
            assert (
                result2["pagination"]["current_page_start"]
                == result["pagination"]["current_page_end"]
            )


class TestSplitAPIEndpoints:
    """Test individual split API endpoint functionality."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        from main_split import app

        return TestClient(app)

    def test_text_endpoint_with_invalid_url(self, client):
        """Test text endpoint error handling."""
        with patch("main_split.get_page_content") as mock_get_content:
            mock_get_content.side_effect = Exception("Connection failed")

            response = client.get("/scrape/text?url=invalid-url")

            assert response.status_code == 500
            data = response.json()
            assert "detail" in data

    def test_media_endpoint_with_type_filter(self, client):
        """Test media endpoint with type filtering."""
        with patch("main_split.get_page_content") as mock_get_content:
            mock_soup = Mock()
            mock_get_content.return_value = (mock_soup, "<html>test</html>", 200)

            with patch("main_split.extract_media_assets") as mock_extract:
                mock_extract.return_value = {
                    "media_assets": [],
                    "media_summary": {
                        "total_assets": 0,
                        "images_count": 0,
                        "videos_count": 0,
                        "documents_count": 0,
                        "icons_count": 0,
                        "current_page_count": 0,
                        "has_more": False,
                    },
                    "pagination": {
                        "next_cursor": None,
                        "has_more": False,
                        "total_count": 0,
                        "current_page_start": 0,
                        "current_page_end": 0,
                    },
                }

                response = client.get(
                    "/scrape/media?url=test.com&media_type=image&limit=10"
                )

                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True

    def test_enhance_endpoint_with_ai(self, client):
        """Test enhance endpoint with AI processing."""
        with patch("main_split.get_page_content") as mock_get_content:
            mock_soup = Mock()
            mock_get_content.return_value = (mock_soup, "<html>test</html>", 200)

            with patch("main_split.extract_company_info_programmatic") as mock_extract:
                mock_extract.return_value = {
                    "title": "Test Company",
                    "description": "Test description",
                    "content": "Test content",
                    "company_info": {"confidence": "medium"},
                    "url": "https://test.com",
                }

                response = client.get("/scrape/enhance?url=test.com")

                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert data["approach_used"] == "ai_enhanced"
                assert "enhanced_content" in data
                assert "ai_insights" in data
