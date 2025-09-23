import json
import os
from io import BytesIO
from unittest.mock import ANY, AsyncMock, Mock, patch

import ffmpeg
import pytest
import requests
from PIL import Image

from api.models import MediaAsset, MediaMetadata
from api.services.media import MediaProcessingError, MediaService


@pytest.fixture
def mock_storage():
    """Create a mock storage service."""
    storage = Mock()
    storage.upload = AsyncMock(return_value="https://cdn.example.com/media/test.jpg")
    return storage


@pytest.fixture
def mock_cache():
    """Create a mock cache service."""
    cache = Mock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    return cache


@pytest.fixture
def media_service(mock_storage, mock_cache):
    """Create a media service instance with mocked dependencies."""
    return MediaService(
        storage=mock_storage,
        cache=mock_cache,
        max_file_size=1024 * 1024,  # 1MB
        max_video_duration=60,  # 1 minute
    )


@pytest.fixture
def sample_image():
    """Create a sample image."""
    img = Image.new("RGB", (100, 100), color="red")
    buffer = BytesIO()
    img.save(buffer, format="JPEG")
    return buffer.getvalue()


@pytest.fixture
def sample_video():
    """Create a sample video metadata."""
    return {
        "streams": [{"codec_type": "video", "width": 1280, "height": 720}],
        "format": {"duration": "30.0"},
    }


def test_init_default_params():
    """Test media service initialization with default parameters."""
    storage = Mock()
    cache = Mock()
    service = MediaService(storage=storage, cache=cache)
    assert service.max_size == 10 * 1024 * 1024  # 10MB
    assert service.max_video_duration == 300  # 5 minutes
    assert "image/jpeg" in service.allowed_image_types
    assert "video/mp4" in service.allowed_video_types


def test_init_custom_params():
    """Test media service initialization with custom parameters."""
    storage = Mock()
    cache = Mock()
    service = MediaService(
        storage=storage,
        cache=cache,
        max_file_size=1024,
        max_video_duration=60,
        supported_image_types=["image/png"],
        supported_video_types=["video/webm"],
    )
    assert service.max_size == 1024
    assert service.max_video_duration == 60
    assert service.allowed_image_types == ["image/png"]
    assert service.allowed_video_types == ["video/webm"]


@pytest.mark.asyncio
async def test_download_media_success(media_service, sample_image):
    """Test successful media download."""
    # Mock requests response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {
        "content-type": "image/jpeg",
        "content-length": str(len(sample_image)),
    }
    mock_response.content = sample_image

    with patch("requests.get", return_value=mock_response):
        asset = await media_service.download_media("https://example.com/image.jpg")
        assert asset.type == "image"
        assert str(asset.url) == "https://example.com/image.jpg"
        assert asset.metadata.width == 100
        assert asset.metadata.height == 100
        assert asset.metadata.format == "jpeg"


@pytest.mark.asyncio
async def test_download_media_from_cache(media_service):
    """Test getting media from cache."""
    # Mock cached data
    cached_data = {
        "type": "image",
        "url": "https://example.com/image.jpg",
        "metadata": {
            "width": 100,
            "height": 100,
            "size_bytes": 1024,
            "format": "jpeg",
            "priority": 80,
            "duration_seconds": None,
        },
        "context": "Test image",
    }
    media_service.cache.get.return_value = json.dumps(cached_data)

    # Mock successful HTTP response
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "image/jpeg", "content-length": "1024"}
    mock_response.content = b"test_image_data"

    with (
        patch("requests.get", return_value=mock_response),
        patch.object(
            media_service,
            "process_image",
            return_value=(
                b"processed_data",
                {"width": 100, "height": 100, "format": "jpeg", "size_bytes": 1024},
            ),
        ),
    ):
        asset = await media_service.download_media("https://example.com/image.jpg")
        assert asset.type == "image"
        assert str(asset.url) == "https://example.com/image.jpg"
        assert asset.metadata.width == 100


@pytest.mark.asyncio
async def test_download_media_http_error(media_service):
    """Test handling of HTTP errors."""
    mock_response = Mock()
    mock_response.status_code = 404

    with patch("requests.get", return_value=mock_response):
        with pytest.raises(
            MediaProcessingError, match="Download failed with status 404"
        ):
            await media_service.download_media("https://example.com/image.jpg")


@pytest.mark.asyncio
async def test_download_media_unsupported_type(media_service):
    """Test handling of unsupported media types."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "text/plain"}

    with patch("requests.get", return_value=mock_response):
        with pytest.raises(MediaProcessingError, match="Unsupported media type"):
            await media_service.download_media("https://example.com/text.txt")


@pytest.mark.asyncio
async def test_download_media_size_limit(media_service):
    """Test handling of files exceeding size limit."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.headers = {
        "content-type": "image/jpeg",
        "content-length": str(2 * 1024 * 1024),  # 2MB
    }

    with patch("requests.get", return_value=mock_response):
        with pytest.raises(MediaProcessingError, match="File size exceeds limit"):
            await media_service.download_media("https://example.com/large.jpg")


@pytest.mark.asyncio
async def test_process_image_success(media_service, sample_image):
    """Test successful image processing."""
    content, metadata = await media_service.process_image(sample_image, "image/jpeg")
    assert len(content) > 0
    assert metadata["width"] == 100
    assert metadata["height"] == 100
    assert metadata["format"] == "jpeg"


@pytest.mark.asyncio
async def test_process_image_svg(media_service):
    """Test SVG image processing."""
    svg_content = b'<svg width="100" height="100"></svg>'

    # Create a valid PNG image for testing
    test_img = Image.new("RGB", (100, 100), color="red")
    png_buffer = BytesIO()
    test_img.save(png_buffer, format="PNG")
    png_data = png_buffer.getvalue()

    with patch("cairosvg.svg2png", return_value=png_data):
        content, metadata = await media_service.process_image(
            svg_content, "image/svg+xml"
        )
        assert content == png_data
        assert metadata["width"] == 100
        assert metadata["height"] == 100
        assert metadata["format"] == "png"


@pytest.mark.asyncio
async def test_process_image_error(media_service):
    """Test handling of image processing errors."""
    with pytest.raises(MediaProcessingError, match="Image processing failed"):
        await media_service.process_image(b"invalid_image", "image/jpeg")


@pytest.mark.asyncio
async def test_process_video_success(media_service, sample_video):
    """Test successful video processing."""
    video_content = b"fake_video_data"

    with (
        patch("ffmpeg.probe", return_value=sample_video),
        patch("builtins.open", create=True),
        patch("os.path.exists", return_value=True),
        patch("os.remove"),
    ):
        content, metadata = await media_service.process_video(
            video_content, "video/mp4"
        )
        assert content == video_content
        assert metadata["width"] == 1280
        assert metadata["height"] == 720
        assert metadata["duration_seconds"] == 30.0


@pytest.mark.asyncio
async def test_process_video_duration_limit(media_service):
    """Test handling of videos exceeding duration limit."""
    video_content = b"fake_video_data"
    long_video = {
        "streams": [{"codec_type": "video", "width": 1280, "height": 720}],
        "format": {"duration": "120.0"},  # 2 minutes
    }

    with (
        patch("ffmpeg.probe", return_value=long_video),
        patch("builtins.open", create=True),
        patch("os.path.exists", return_value=True),
        patch("os.remove"),
    ):
        with pytest.raises(MediaProcessingError, match="Video duration exceeds limit"):
            await media_service.process_video(video_content, "video/mp4")


@pytest.mark.asyncio
async def test_process_video_probe_error(media_service):
    """Test handling of video probe errors."""
    video_content = b"fake_video_data"

    with (
        patch(
            "ffmpeg.probe",
            side_effect=ffmpeg.Error(
                "Probe failed", stdout=b"", stderr=b"Error probing video"
            ),
        ),
        patch("builtins.open", create=True),
        patch("os.path.exists", return_value=True),
        patch("os.remove"),
    ):
        with pytest.raises(MediaProcessingError, match="Failed to probe video file"):
            await media_service.process_video(video_content, "video/mp4")


@pytest.mark.asyncio
async def test_store_media_success(media_service):
    """Test successful media storage."""
    media_data = b"test_data"
    url = await media_service.store_media(
        media_data, "image/jpeg", "https://example.com/image.jpg"
    )
    assert url == "https://cdn.example.com/media/test.jpg"
    media_service.storage.upload.assert_called_once()


@pytest.mark.asyncio
async def test_store_media_error(media_service):
    """Test handling of storage errors."""
    media_service.storage.upload.side_effect = Exception("Storage error")

    with pytest.raises(MediaProcessingError, match="Failed to store media"):
        await media_service.store_media(
            b"test_data", "image/jpeg", "https://example.com/image.jpg"
        )


@pytest.mark.asyncio
async def test_get_cached_media_success(media_service):
    """Test successful cache retrieval."""
    cached_data = {
        "type": "image",
        "url": "https://example.com/image.jpg",
        "metadata": {
            "width": 100,
            "height": 100,
            "size_bytes": 1024,
            "format": "jpeg",
            "priority": 80,
            "duration_seconds": None,
        },
        "context": "Test image",
    }
    media_service.cache.get.return_value = json.dumps(cached_data)

    asset = await media_service.get_cached_media("https://example.com/image.jpg")
    assert asset is not None
    assert asset.type == "image"
    assert str(asset.url) == "https://example.com/image.jpg"


@pytest.mark.asyncio
async def test_get_cached_media_not_found(media_service):
    """Test cache miss."""
    media_service.cache.get.return_value = None
    asset = await media_service.get_cached_media("https://example.com/image.jpg")
    assert asset is None


@pytest.mark.asyncio
async def test_get_cached_media_error(media_service):
    """Test handling of cache errors."""
    media_service.cache.get.side_effect = Exception("Cache error")
    asset = await media_service.get_cached_media("https://example.com/image.jpg")
    assert asset is None


@pytest.mark.asyncio
async def test_update_cache_success(media_service):
    """Test successful cache update."""
    asset = MediaAsset(
        type="image",
        url="https://example.com/image.jpg",
        metadata=MediaMetadata(
            width=100,
            height=100,
            size_bytes=1024,
            format="jpeg",
            priority=80,
            duration_seconds=None,
        ),
        context="Test image",
    )

    await media_service.update_cache("https://example.com/image.jpg", asset)
    media_service.cache.set.assert_called_once()


@pytest.mark.asyncio
async def test_update_cache_error(media_service):
    """Test handling of cache update errors."""
    media_service.cache.set.side_effect = Exception("Cache error")

    asset = MediaAsset(
        type="image",
        url="https://example.com/image.jpg",
        metadata=MediaMetadata(
            width=100,
            height=100,
            size_bytes=1024,
            format="jpeg",
            priority=80,
            duration_seconds=None,
        ),
        context="Test image",
    )

    # Should not raise exception
    await media_service.update_cache("https://example.com/image.jpg", asset)
