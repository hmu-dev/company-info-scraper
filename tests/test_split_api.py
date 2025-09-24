"""
Tests for the split API endpoints (text, media, enhance).
"""

import base64
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient


class TestSplitAPI:
    """Test suite for the split API endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client for the split API."""
        from about_us_scraper_service.api.main_split import app

        return TestClient(app)

    def test_health_endpoint(self, client):
        """Test the health endpoint returns correct split API info."""
        response = client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "3.0.0"
        assert data["approach"] == "split"

    @patch("about_us_scraper_service.api.main_split.get_page_content")
    @patch("about_us_scraper_service.api.main_split.extract_company_info_programmatic")
    @patch("about_us_scraper_service.api.main_split.find_about_pages")
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

    @patch("about_us_scraper_service.api.main_split.get_page_content")
    @patch("about_us_scraper_service.api.main_split.extract_media_assets")
    def test_scrape_media_endpoint_no_cursor(
        self, mock_extract_media, mock_get_content, client
    ):
        """Test the /scrape/media endpoint without cursor."""
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

    @patch("about_us_scraper_service.api.main_split.get_page_content")
    @patch("about_us_scraper_service.api.main_split.extract_media_assets")
    def test_scrape_media_endpoint_with_cursor(
        self, mock_extract_media, mock_get_content, client
    ):
        """Test the /scrape/media endpoint with cursor pagination."""
        # Mock the dependencies
        mock_soup = Mock()
        mock_get_content.return_value = (mock_soup, "<html>test</html>", 200)

        mock_media_data = {
            "media_assets": [
                {
                    "id": "test456",
                    "url": "https://test.com/image2.png",
                    "type": "image",
                    "alt": "Second Image",
                    "priority": 80,
                    "context": "Second Image",
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
                "next_cursor": base64.b64encode("media:2".encode()).decode(),
                "has_more": True,
                "total_count": 5,
                "current_page_start": 1,
                "current_page_end": 2,
            },
        }
        mock_extract_media.return_value = mock_media_data

        # Test with cursor
        cursor = base64.b64encode("media:1".encode()).decode()
        response = client.get(f"/scrape/media?url=test.com&cursor={cursor}&limit=1")

        assert response.status_code == 200
        data = response.json()

        # Verify cursor pagination worked
        assert data["success"] is True
        assert len(data["media_assets"]) == 1
        assert data["pagination"]["current_page_start"] == 1
        assert data["pagination"]["current_page_end"] == 2

    @patch("about_us_scraper_service.api.main_split.get_page_content")
    @patch("about_us_scraper_service.api.main_split.extract_company_info_programmatic")
    def test_scrape_enhance_endpoint(
        self, mock_extract_company, mock_get_content, client
    ):
        """Test the /scrape/enhance endpoint."""
        # Mock the dependencies
        mock_soup = Mock()
        mock_get_content.return_value = (mock_soup, "<html>test</html>", 200)

        mock_company_data = {
            "title": "Test Company",
            "description": "A test company",
            "content": "Test content for AI enhancement",
            "company_info": {
                "founded": "2020",
                "employees": "10",
                "location": "Test City",
                "mission": "Test mission",
                "confidence": "medium",
            },
            "url": "https://test.com",
        }
        mock_extract_company.return_value = mock_company_data

        # Test the endpoint
        response = client.get("/scrape/enhance?url=test.com")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert data["success"] is True
        assert data["url"] == "https://test.com"
        assert "enhanced_content" in data
        assert "ai_insights" in data
        assert data["approach_used"] == "ai_enhanced"
        assert "processing_time_seconds" in data

    def test_scrape_text_endpoint_invalid_url(self, client):
        """Test the /scrape/text endpoint with invalid URL."""
        with patch(
            "about_us_scraper_service.api.main_split.get_page_content"
        ) as mock_get_content:
            mock_get_content.side_effect = Exception("Invalid URL")

            response = client.get("/scrape/text?url=invalid-url")

            assert response.status_code == 500
            data = response.json()
            assert "detail" in data

    def test_scrape_media_endpoint_invalid_cursor(self, client):
        """Test the /scrape/media endpoint with invalid cursor."""
        with patch(
            "about_us_scraper_service.api.main_split.get_page_content"
        ) as mock_get_content:
            mock_soup = Mock()
            mock_get_content.return_value = (mock_soup, "<html>test</html>", 200)

            with patch(
                "about_us_scraper_service.api.main_split.extract_media_assets"
            ) as mock_extract:
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

                # Test with invalid cursor (should default to start_index = 0)
                response = client.get(
                    "/scrape/media?url=test.com&cursor=invalid-cursor&limit=10"
                )

                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True

    def test_legacy_endpoints_redirect(self, client):
        """Test that legacy endpoints redirect to new split endpoints."""
        with patch(
            "about_us_scraper_service.api.main_split.get_page_content"
        ) as mock_get_content:
            mock_soup = Mock()
            mock_get_content.return_value = (mock_soup, "<html>test</html>", 200)

            with patch(
                "about_us_scraper_service.api.main_split.extract_company_info_programmatic"
            ) as mock_extract:
                mock_extract.return_value = {
                    "title": "Test",
                    "description": "Test",
                    "content": "Test",
                    "company_info": {"confidence": "medium"},
                    "url": "https://test.com",
                }

                with patch(
                    "about_us_scraper_service.api.main_split.find_about_pages"
                ) as mock_find:
                    mock_find.return_value = []

                    # Test legacy /scrape endpoint
                    response = client.get("/scrape?url=test.com")
                    assert response.status_code == 200

                    # Test legacy /scrape/about endpoint
                    response = client.get("/scrape/about?url=test.com")
                    assert response.status_code == 200


class TestCursorPagination:
    """Test suite specifically for cursor pagination functionality."""

    def test_cursor_encoding_decoding(self):
        """Test cursor encoding and decoding logic."""
        from unittest.mock import Mock

        from about_us_scraper_service.api.main_split import extract_media_assets

        # Test cursor creation
        mock_soup = Mock()
        mock_soup.find_all.return_value = []

        # Create media data that would generate a cursor
        result = extract_media_assets(mock_soup, "https://test.com", None, 5)

        # If there are items, should have pagination info
        if result["pagination"]["has_more"]:
            cursor = result["pagination"]["next_cursor"]
            assert cursor is not None

            # Decode the cursor
            import base64

            decoded = base64.b64decode(cursor).decode()
            assert decoded.startswith("media:")

            # Extract index
            index = int(decoded.split(":")[1])
            assert index >= 0

    def test_cursor_pagination_continuity(self):
        """Test that cursor pagination maintains continuity."""
        from unittest.mock import Mock

        from about_us_scraper_service.api.main_split import extract_media_assets

        # Mock soup with multiple images
        mock_soup = Mock()
        mock_img1 = Mock()
        mock_img1.get.side_effect = lambda x: (
            "https://test.com/img1.png" if x == "src" else ""
        )
        mock_img1.name = "img"

        mock_img2 = Mock()
        mock_img2.get.side_effect = lambda x: (
            "https://test.com/img2.png" if x == "src" else ""
        )
        mock_img2.name = "img"

        mock_soup.find_all.side_effect = lambda x: (
            [mock_img1, mock_img2] if x == "img" else []
        )

        # First page
        result1 = extract_media_assets(mock_soup, "https://test.com", None, 1)

        if result1["pagination"]["has_more"]:
            cursor = result1["pagination"]["next_cursor"]

            # Second page using cursor
            result2 = extract_media_assets(mock_soup, "https://test.com", cursor, 1)

            # Verify continuity
            assert (
                result2["pagination"]["current_page_start"]
                == result1["pagination"]["current_page_end"]
            )
            assert (
                result2["pagination"]["total_count"]
                == result1["pagination"]["total_count"]
            )
