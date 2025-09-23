from datetime import datetime, timezone

import pytest
from pydantic import HttpUrl, ValidationError

from api.models import (
    BaseResponse,
    CompanyProfile,
    ErrorResponse,
    MediaAsset,
    MediaMetadata,
    MediaResponse,
    PaginationMeta,
    ProfileResponse,
    ScrapeRequest,
    TokenUsage,
)


def test_company_profile():
    """Test CompanyProfile model."""
    data = {
        "about_us": "About text",
        "our_culture": "Culture text",
        "our_team": "Team text",
        "noteworthy_and_differentiated": "Features text",
        "locations": "Location text",
    }
    profile = CompanyProfile(**data)
    assert profile.about_us == "About text"
    assert profile.our_culture == "Culture text"
    assert profile.our_team == "Team text"
    assert profile.noteworthy_and_differentiated == "Features text"
    assert profile.locations == "Location text"


def test_media_metadata():
    """Test MediaMetadata model."""
    data = {
        "width": 800,
        "height": 600,
        "size_bytes": 1024,
        "format": "jpeg",
        "priority": 80,
        "duration_seconds": None,
    }
    metadata = MediaMetadata(**data)
    assert metadata.width == 800
    assert metadata.height == 600
    assert metadata.size_bytes == 1024
    assert metadata.format == "jpeg"
    assert metadata.priority == 80
    assert metadata.duration_seconds is None


def test_media_metadata_validation():
    """Test MediaMetadata validation."""
    # Test invalid size_bytes
    with pytest.raises(ValidationError) as exc:
        MediaMetadata(size_bytes=0, format="jpeg", priority=80)
    assert "size_bytes" in str(exc.value)

    # Test invalid priority
    with pytest.raises(ValidationError) as exc:
        MediaMetadata(size_bytes=1024, format="jpeg", priority=101)
    assert "priority" in str(exc.value)

    # Test invalid duration_seconds
    with pytest.raises(ValidationError) as exc:
        MediaMetadata(size_bytes=1024, format="jpeg", priority=80, duration_seconds=0)
    assert "duration_seconds" in str(exc.value)


def test_media_asset():
    """Test MediaAsset model."""
    data = {
        "url": "https://example.com/image.jpg",
        "type": "image",
        "metadata": {
            "width": 800,
            "height": 600,
            "size_bytes": 1024,
            "format": "jpeg",
            "priority": 80,
            "duration_seconds": None,
        },
        "context": "Header image",
    }
    asset = MediaAsset(**data)
    assert str(asset.url) == "https://example.com/image.jpg"
    assert asset.type == "image"
    assert asset.metadata.width == 800
    assert asset.context == "Header image"


def test_media_asset_validation():
    """Test MediaAsset validation."""
    # Test invalid URL
    with pytest.raises(ValidationError) as exc:
        MediaAsset(
            url="not-a-url",
            type="image",
            metadata={"size_bytes": 1024, "format": "jpeg", "priority": 80},
            context="Test",
        )
    assert "url" in str(exc.value)

    # Test invalid type
    with pytest.raises(ValidationError) as exc:
        MediaAsset(
            url="https://example.com/image.jpg",
            type="invalid",
            metadata={"size_bytes": 1024, "format": "jpeg", "priority": 80},
            context="Test",
        )
    assert "type" in str(exc.value)


def test_pagination_meta():
    """Test PaginationMeta model."""
    data = {
        "next_cursor": "next-page",
        "has_more": True,
        "total_count": 100,
        "remaining_count": 80,
    }
    pagination = PaginationMeta(**data)
    assert pagination.next_cursor == "next-page"
    assert pagination.has_more is True
    assert pagination.total_count == 100
    assert pagination.remaining_count == 80


def test_pagination_meta_validation():
    """Test PaginationMeta validation."""
    # Test invalid total_count
    with pytest.raises(ValidationError) as exc:
        PaginationMeta(has_more=True, total_count=-1, remaining_count=0)
    assert "total_count" in str(exc.value)

    # Test invalid remaining_count
    with pytest.raises(ValidationError) as exc:
        PaginationMeta(has_more=True, total_count=100, remaining_count=-1)
    assert "remaining_count" in str(exc.value)


def test_scrape_request():
    """Test ScrapeRequest model."""
    data = {
        "url": "https://example.com",
        "model": "anthropic.claude-instant-v1",
        "cursor": "next-page",
        "limit": 20,
    }
    request = ScrapeRequest(**data)
    assert str(request.url).rstrip("/") == "https://example.com"
    assert request.model == "anthropic.claude-instant-v1"
    assert request.cursor == "next-page"
    assert request.limit == 20
    assert request.openai_api_key is None


def test_scrape_request_validation():
    """Test ScrapeRequest validation."""
    # Test invalid URL
    with pytest.raises(ValidationError) as exc:
        ScrapeRequest(url="not-a-url", model="anthropic.claude-instant-v1")
    assert "url" in str(exc.value)

    # Test invalid model
    with pytest.raises(ValidationError) as exc:
        ScrapeRequest(url="https://example.com", model="invalid-model")
    assert "model" in str(exc.value)

    # Test invalid limit
    with pytest.raises(ValidationError) as exc:
        ScrapeRequest(
            url="https://example.com", model="anthropic.claude-instant-v1", limit=0
        )
    assert "limit" in str(exc.value)

    # Test URL too long
    long_url = "https://example.com/" + "a" * 2048
    with pytest.raises(ValidationError) as exc:
        ScrapeRequest(url=long_url, model="anthropic.claude-instant-v1")
    assert "URL too long" in str(exc.value)


def test_token_usage():
    """Test TokenUsage model."""
    data = {"prompt_tokens": 100, "completion_tokens": 50}
    usage = TokenUsage(**data)
    assert usage.prompt_tokens == 100
    assert usage.completion_tokens == 50


def test_token_usage_validation():
    """Test TokenUsage validation."""
    # Test invalid prompt_tokens
    with pytest.raises(ValidationError) as exc:
        TokenUsage(prompt_tokens=-1, completion_tokens=0)
    assert "prompt_tokens" in str(exc.value)

    # Test invalid completion_tokens
    with pytest.raises(ValidationError) as exc:
        TokenUsage(prompt_tokens=0, completion_tokens=-1)
    assert "completion_tokens" in str(exc.value)


def test_base_response():
    """Test BaseResponse model."""
    data = {"success": True, "duration": 1.5}
    response = BaseResponse(**data)
    assert response.success is True
    assert response.duration == 1.5


def test_base_response_validation():
    """Test BaseResponse validation."""
    # Test invalid duration
    with pytest.raises(ValidationError) as exc:
        BaseResponse(success=True, duration=-1.0)
    assert "duration" in str(exc.value)


def test_profile_response():
    """Test ProfileResponse model."""
    data = {
        "success": True,
        "duration": 1.5,
        "data": {
            "about_us": "About text",
            "our_culture": "Culture text",
            "our_team": "Team text",
            "noteworthy_and_differentiated": "Features text",
            "locations": "Location text",
        },
        "token_usage": {"prompt_tokens": 100, "completion_tokens": 50},
    }
    response = ProfileResponse(**data)
    assert response.success is True
    assert response.duration == 1.5
    assert response.data.about_us == "About text"
    assert response.token_usage.prompt_tokens == 100


def test_media_response():
    """Test MediaResponse model."""
    data = {
        "success": True,
        "duration": 1.5,
        "url_scraped": "https://example.com",
        "media": [
            {
                "url": "https://example.com/image.jpg",
                "type": "image",
                "metadata": {
                    "width": 800,
                    "height": 600,
                    "size_bytes": 1024,
                    "format": "jpeg",
                    "priority": 80,
                    "duration_seconds": None,
                },
                "context": "Header image",
            }
        ],
        "pagination": {
            "next_cursor": "next-page",
            "has_more": True,
            "total_count": 100,
            "remaining_count": 80,
        },
    }
    response = MediaResponse(**data)
    assert response.success is True
    assert response.duration == 1.5
    assert str(response.url_scraped).rstrip("/") == "https://example.com"
    assert len(response.media) == 1
    assert response.media[0].type == "image"
    assert response.pagination.has_more is True


def test_error_response():
    """Test ErrorResponse model."""
    data = {
        "error": "Something went wrong",
        "error_type": "ValueError",
        "request_id": "123",
        "timestamp": datetime.now(timezone.utc),
    }
    response = ErrorResponse(**data)
    assert response.success is False
    assert response.error == "Something went wrong"
    assert response.error_type == "ValueError"
    assert response.request_id == "123"
    assert isinstance(response.timestamp, datetime)


def test_error_response_defaults():
    """Test ErrorResponse default values."""
    data = {
        "error": "Something went wrong",
        "error_type": "ValueError",
        "request_id": "123",
    }
    response = ErrorResponse(**data)
    assert response.success is False
    assert isinstance(response.timestamp, datetime)
