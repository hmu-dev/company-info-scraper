import pytest
from fastapi import Response
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock, patch
from api.endpoints.media import router, calculate_priority
from api.models import ScrapeRequest, MediaAsset, MediaMetadata
from api.utils.storage import MediaStorage, StorageError
from api.utils.pagination import PaginationMeta
from pydantic import HttpUrl


@pytest.fixture
def client():
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


@pytest.fixture
def mock_storage():
    with patch("api.endpoints.media.MediaStorage") as mock:
        storage_instance = Mock(spec=MediaStorage)
        storage_instance.store_media = AsyncMock(
            return_value=(
                "https://cdn.example.com/logo.png",
                {
                    "width": 200,
                    "height": 200,
                    "size_bytes": 15000,
                    "format": "png",
                    "filename": "logo.png",
                    "duration_seconds": None,
                },
            )
        )
        storage_instance.bucket_name = "test-bucket"
        storage_instance.cloudfront_domain = "test.cloudfront.net"
        mock.return_value = storage_instance
        yield storage_instance


@pytest.fixture
def mock_extract_media():
    with patch("api.endpoints.media.extract_media_from_html") as mock:
        mock.return_value = [
            ("https://example.com/logo.png", "image", "Company logo"),
            ("https://example.com/team.jpg", "image", "Our team"),
            ("https://example.com/office.jpg", "image", "Office location"),
        ]
        yield mock


@pytest.fixture
def mock_paginate():
    with patch("api.endpoints.media.paginate_items") as mock:
        mock.return_value = Mock(
            items=[
                MediaAsset(
                    url=HttpUrl("https://cdn.example.com/logo.png"),
                    type="image",
                    metadata=MediaMetadata(
                        width=200,
                        height=200,
                        size_bytes=15000,
                        format="png",
                        priority=95,  # Updated to match new priority calculation
                        duration_seconds=None,
                    ),
                    context="Company logo",  # Added context for priority calculation
                )
            ],
            pagination=PaginationMeta(
                total_count=3, remaining_count=2, has_more=True, next_cursor="next_page"
            ),
        )
        yield mock


def test_scrape_media_success(client, mock_storage, mock_extract_media, mock_paginate):
    # Setup

    # Execute
    response = client.post(
        "/media",
        json={
            "url": "https://example.com",
            "include_base64": False,
            "cursor": None,
            "limit": 10,
        },
    )

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["url_scraped"] == "https://example.com/"
    assert "duration" in data
    assert data["duration"] >= 0
    assert len(data["media"]) == 1
    assert data["media"][0]["url"] == "https://cdn.example.com/logo.png"
    assert data["media"][0]["type"] == "image"
    assert data["media"][0]["context"] == "Company logo"
    assert (
        data["media"][0]["metadata"]["priority"] == 95
    )  # Updated to match new priority calculation
    assert data["pagination"]["total_count"] == 3
    assert data["pagination"]["remaining_count"] == 2
    assert data["pagination"]["has_more"] is True
    assert data["pagination"]["next_cursor"] == "next_page"


def test_scrape_media_storage_error(
    client, mock_storage, mock_extract_media, mock_paginate
):
    # Setup
    mock_storage.store_media = AsyncMock(
        side_effect=StorageError("Failed to store media")
    )
    mock_extract_media.return_value = [
        ("https://example.com/logo.png", "image", "Company logo")
    ]

    # Execute
    response = client.post(
        "/media",
        json={
            "url": "https://example.com",
            "include_base64": False,
            "cursor": None,
            "limit": 10,
        },
    )

    # Assert
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert "error" in data["detail"]
    assert data["detail"]["error_type"] == "HTTPException"
    assert "Failed to store media" in data["detail"]["error"]


def test_scrape_media_invalid_request(client):
    # Execute
    response = client.post(
        "/media",
        json={"url": "not-a-url", "include_base64": False, "cursor": None, "limit": 10},
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


def test_calculate_priority_logo():
    metadata = {"width": 200, "height": 200}
    priority = calculate_priority("Company logo", metadata)
    assert priority == 95  # 80 (logo) + 15 (square aspect ratio)


def test_calculate_priority_team():
    metadata = {"width": 1200, "height": 800}
    priority = calculate_priority("Our team photo", metadata)
    assert priority == 65  # 60 (team) + 5 (high resolution)


def test_calculate_priority_office():
    metadata = {"width": 800, "height": 600}
    priority = calculate_priority("Office location", metadata)
    assert priority == 40  # 40 (office)


def test_calculate_priority_product():
    metadata = {"width": 1000, "height": 1000}
    priority = calculate_priority("Product showcase", metadata)
    assert priority == 50  # 30 (product) + 15 (square) + 5 (high res)


def test_calculate_priority_default():
    metadata = {"width": 400, "height": 300}
    priority = calculate_priority("Generic image", metadata)
    assert priority == 10  # default score


def test_calculate_priority_no_dimensions():
    metadata = {}
    priority = calculate_priority("Company logo", metadata)
    assert priority == 80  # logo score only, no metadata boosts
