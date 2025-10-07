"""
Tests for the AI Web Scraper API - Version 4.0
Tests the remote team compatible schema format.
"""

import base64
import json
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient


class TestAPIV4:
    """Test suite for the API v4.0 with remote team compatible schema."""

    @pytest.fixture
    def client(self):
        """Create a test client for the API v4.0."""
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'about-us-scraper-service'))
        from api.main_v4 import app

        return TestClient(app)

    def test_health_endpoint(self, client):
        """Test the health endpoint returns correct v4 info."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "4.0.0"
        assert data["approach"] == "remote_team_compatible"

    @patch("api.main_v4.get_page_content")
    def test_scrape_text_endpoint_schema_compliance(
        self, mock_get_content, client
    ):
        """Test that the /scrape/text endpoint returns the correct schema."""
        # Mock the dependencies
        mock_soup = Mock()
        mock_soup.find.return_value = Mock(get_text=lambda: "Test Company")
        mock_soup.get_text.return_value = "Test content about the company"
        mock_soup.find_all.return_value = []
        mock_get_content.return_value = (mock_soup, "<html>test</html>", 200)

        # Test the endpoint
        response = client.get("/scrape/text?url=test.com")

        assert response.status_code == 200
        data = response.json()

        # Verify top-level schema compliance
        assert "statusCode" in data
        assert "message" in data
        assert "scrapingData" in data

        assert data["statusCode"] == 200
        assert data["message"] == "URL scraping completed successfully"

        # Verify scrapingData structure
        scraping_data = data["scrapingData"]
        required_fields = [
            "page_title",
            "url",
            "language",
            "summary",
            "sections",
            "key_values",
            "media",
            "notes",
        ]
        for field in required_fields:
            assert field in scraping_data, f"Missing required field: {field}"

        # Verify sections format
        assert isinstance(scraping_data["sections"], list)
        if scraping_data["sections"]:
            section = scraping_data["sections"][0]
            assert "name" in section
            assert "content_summary" in section
            assert "raw_excerpt" in section

        # Verify key_values format
        assert isinstance(scraping_data["key_values"], list)
        if scraping_data["key_values"]:
            kv = scraping_data["key_values"][0]
            assert "key" in kv
            assert "value" in kv

        # Verify media format
        assert isinstance(scraping_data["media"], dict)
        assert "images" in scraping_data["media"]
        assert "videos" in scraping_data["media"]
        assert isinstance(scraping_data["media"]["images"], list)
        assert isinstance(scraping_data["media"]["videos"], list)

    @patch("api.main_v4.get_page_content")
    def test_scrape_text_endpoint_with_real_data_structure(
        self, mock_get_content, client
    ):
        """Test the endpoint with realistic data structure."""
        # Mock a more realistic response
        mock_soup = Mock()
        mock_soup.find.return_value = Mock(get_text=lambda: "About Test Company")
        mock_soup.get_text.return_value = "Founded in 2020, Test Company is based in San Francisco. We specialize in technology solutions."
        mock_soup.find_all.return_value = []

        # Mock language detection
        mock_html_tag = Mock()
        mock_html_tag.get.return_value = "en"
        mock_soup.find.side_effect = lambda tag, **kwargs: mock_html_tag if tag == "html" else None

        mock_get_content.return_value = (mock_soup, "<html>test</html>", 200)

        response = client.get("/scrape/text?url=test.com")

        assert response.status_code == 200
        data = response.json()

        # Verify the response matches the expected schema exactly
        expected_structure = {
            "statusCode": 200,
            "message": "URL scraping completed successfully",
            "scrapingData": {
                "page_title": "About Test Company",
                "url": "https://test.com",
                "language": "en",
                "summary": str,
                "sections": list,
                "key_values": list,
                "media": {"images": list, "videos": list},
                "notes": str,
            },
        }

        # Verify structure
        assert data["statusCode"] == expected_structure["statusCode"]
        assert data["message"] == expected_structure["message"]

        scraping_data = data["scrapingData"]
        assert scraping_data["page_title"] == expected_structure["scrapingData"]["page_title"]
        assert scraping_data["url"] == expected_structure["scrapingData"]["url"]
        assert scraping_data["language"] == expected_structure["scrapingData"]["language"]
        assert isinstance(scraping_data["summary"], expected_structure["scrapingData"]["summary"])
        assert isinstance(scraping_data["sections"], expected_structure["scrapingData"]["sections"])
        assert isinstance(scraping_data["key_values"], expected_structure["scrapingData"]["key_values"])
        assert scraping_data["media"] == expected_structure["scrapingData"]["media"]
        assert isinstance(scraping_data["notes"], expected_structure["scrapingData"]["notes"])

    def test_scrape_text_endpoint_invalid_url(self, client):
        """Test the endpoint with invalid URL returns proper error schema."""
        with patch(
            "api.main_v4.get_page_content"
        ) as mock_get_content:
            mock_get_content.side_effect = Exception("Invalid URL")

            response = client.get("/scrape/text?url=invalid-url")

            assert response.status_code == 200  # FastAPI returns 200 with error in body
            data = response.json()

            # Verify error schema compliance
            assert data["statusCode"] == 500
            assert "message" in data
            assert "scrapingData" in data
            assert data["scrapingData"] is None

    def test_scrape_text_endpoint_with_parameters(self, client):
        """Test the endpoint with custom parameters."""
        with patch(
            "api.main_v4.get_page_content"
        ) as mock_get_content:
            mock_soup = Mock()
            mock_soup.find.return_value = Mock(get_text=lambda: "Test Company")
            mock_soup.get_text.return_value = "Test content"
            mock_soup.find_all.return_value = []
            mock_get_content.return_value = (mock_soup, "<html>test</html>", 200)

            response = client.get(
                "/scrape/text?url=test.com&max_sections=5&max_key_values=3"
            )

            assert response.status_code == 200
            data = response.json()

            # Verify parameters are respected
            scraping_data = data["scrapingData"]
            assert len(scraping_data["sections"]) <= 5
            assert len(scraping_data["key_values"]) <= 3

    def test_lambda_handler_v4_integration(self):
        """Test the lambda handler with a valid API Gateway event."""
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'about-us-scraper-service'))
        from api.lambda_handler_v4 import lambda_handler

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
        assert body["version"] == "4.0.0"
        assert body["approach"] == "remote_team_compatible"

    def test_root_endpoint(self, client):
        """Test the root endpoint returns API information."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()

        assert data["message"] == "AI Web Scraper API - Version 4.0"
        assert data["version"] == "4.0.0"
        assert data["description"] == "Remote team compatible schema"
        assert "/docs" in data["docs"]
        assert "/health" in data["health"]


class TestSchemaCompliance:
    """Test schema compliance with remote team requirements."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        import sys
        import os
        sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'about-us-scraper-service'))
        from api.main_v4 import app

        return TestClient(app)

    def test_schema_matches_remote_team_example(self, client):
        """Test that our schema exactly matches the remote team example."""
        with patch(
            "api.main_v4.get_page_content"
        ) as mock_get_content:
            # Mock realistic data that matches the Ambiance SF example
            mock_soup = Mock()
            mock_soup.find.return_value = Mock(get_text=lambda: "About Ambiance San Francisco | Women's Boutique Locations – Ambiance SF")
            mock_soup.get_text.return_value = "Founded in 1996, our store is located in San Francisco's hottest shopping neighborhoods. Ambiance San Francisco is a women's boutique with multiple locations in San Francisco."
            mock_soup.find_all.return_value = []

            # Mock language detection
            mock_html_tag = Mock()
            mock_html_tag.get.return_value = "en"
            mock_soup.find.side_effect = lambda tag, **kwargs: mock_html_tag if tag == "html" else None

            mock_get_content.return_value = (mock_soup, "<html>test</html>", 200)

            response = client.get("/scrape/text?url=ambiancesf.com/pages/about")

            assert response.status_code == 200
            data = response.json()

            # Verify exact schema compliance
            required_top_level = ["statusCode", "message", "scrapingData"]
            for field in required_top_level:
                assert field in data, f"Missing top-level field: {field}"

            scraping_data = data["scrapingData"]
            required_data_fields = [
                "page_title", "url", "language", "summary", 
                "sections", "key_values", "media", "notes"
            ]
            for field in required_data_fields:
                assert field in scraping_data, f"Missing scrapingData field: {field}"

            # Verify sections array structure
            assert isinstance(scraping_data["sections"], list)
            if scraping_data["sections"]:
                section = scraping_data["sections"][0]
                required_section_fields = ["name", "content_summary", "raw_excerpt"]
                for field in required_section_fields:
                    assert field in section, f"Missing section field: {field}"

            # Verify key_values array structure
            assert isinstance(scraping_data["key_values"], list)
            if scraping_data["key_values"]:
                kv = scraping_data["key_values"][0]
                required_kv_fields = ["key", "value"]
                for field in required_kv_fields:
                    assert field in kv, f"Missing key_value field: {field}"

            # Verify media object structure
            media = scraping_data["media"]
            assert isinstance(media, dict)
            assert "images" in media
            assert "videos" in media
            assert isinstance(media["images"], list)
            assert isinstance(media["videos"], list)
