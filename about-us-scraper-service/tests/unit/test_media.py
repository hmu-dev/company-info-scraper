"""
Unit tests for media.py
"""

import json
from unittest.mock import Mock, patch, AsyncMock
import pytest
from api.services.media import MediaService
from api.utils.retry import MediaProcessingError
from api.utils.storage import MediaStorage
from api.models import MediaAsset, MediaMetadata


@pytest.fixture
def mock_storage():
    storage = Mock()
    storage.upload = AsyncMock()
    storage.download = AsyncMock()
    storage.delete = AsyncMock()
    storage.get_url = Mock()
    return storage


@pytest.fixture
def mock_cache():
    cache = Mock()
    cache.get = AsyncMock()
    cache.set = AsyncMock()
    cache.delete = AsyncMock()
    return cache


@pytest.fixture
def media_service(mock_storage, mock_cache):
    return MediaService(
        storage=mock_storage,
        cache=mock_cache,
        max_file_size=10 * 1024 * 1024,  # 10MB
        max_video_duration=300,  # 5 minutes
        supported_image_types=[
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/webp",
            "image/svg+xml",
        ],
        supported_video_types=["video/mp4", "video/webm"],
    )


@pytest.fixture
def mock_image_response():
    response = Mock()
    response.content = b"test image data"
    response.headers = {"content-type": "image/jpeg", "content-length": "1024"}
    return response


@pytest.fixture
def mock_video_response():
    response = Mock()
    response.content = b"test video data"
    response.headers = {"content-type": "video/mp4", "content-length": "1024"}
    return response


@pytest.fixture
def mock_ffprobe_result():
    return {
        "streams": [
            {"codec_type": "video", "width": 1920, "height": 1080, "duration": "120.5"}
        ],
        "format": {"duration": "120.5", "size": "1024"},
    }


@patch("api.services.media.requests.get")
async def test_download_image_success(mock_get, media_service, mock_image_response):
    """Test successful image download"""
    # Setup
    mock_get.return_value = mock_image_response
    mock_image_response.status_code = 200
    # Create a small test image
    from PIL import Image
    from io import BytesIO

    img = Image.new("RGB", (100, 100), color="red")
    img_bytes = BytesIO()
    img.save(img_bytes, format="JPEG")
    mock_image_response.content = img_bytes.getvalue()
    mock_image_response.headers = {
        "content-type": "image/jpeg",
        "content-length": "1024",
    }
    url = "https://example.com/image.jpg"

    # Mock storage
    media_service.storage.upload.return_value = "https://cdn.example.com/image.jpg"

    # Execute
    media_asset = await media_service.download_media(url)

    # Assert
    assert isinstance(media_asset, MediaAsset)
    assert media_asset.type == "image"
    assert str(media_asset.url) == url
    assert media_asset.metadata.width == 100
    assert media_asset.metadata.height == 100
    assert media_asset.metadata.size_bytes == len(mock_image_response.content)
    assert media_asset.metadata.format == "jpeg"
    assert media_asset.metadata.priority == 80
    assert media_asset.metadata.duration_seconds is None
    mock_get.assert_called_once_with(url, timeout=30)


@patch("api.services.media.requests.get")
async def test_download_video_success(
    mock_get, media_service, mock_video_response, mock_ffprobe_result
):
    """Test successful video download"""
    # Setup
    mock_get.return_value = mock_video_response
    mock_video_response.status_code = 200
    # Create a small test video
    mock_video_response.content = b"test video data"
    mock_video_response.headers = {
        "content-type": "video/mp4",
        "content-length": str(len(mock_video_response.content)),
    }
    url = "https://example.com/video.mp4"
    with patch("ffmpeg.probe") as mock_ffprobe:
        mock_ffprobe.return_value = mock_ffprobe_result

        # Execute
        media_asset = await media_service.download_media(url)

        # Assert
        assert isinstance(media_asset, MediaAsset)
        assert media_asset.type == "video"
        assert str(media_asset.url) == url
        assert media_asset.metadata.format == "mp4"
        assert media_asset.metadata.size_bytes == len(mock_video_response.content)
        assert media_asset.metadata.duration_seconds == 120.5
        assert media_asset.metadata.width == 1920
        assert media_asset.metadata.height == 1080
        mock_get.assert_called_once_with(url, timeout=30)
        mock_ffprobe.assert_called_once()


@patch("api.services.media.requests.get")
async def test_download_media_unsupported_type(mock_get, media_service):
    """Test handling of unsupported media type"""
    # Setup
    response = Mock()
    response.status_code = 200
    response.headers = {"content-type": "application/pdf"}
    mock_get.return_value = response
    url = "https://example.com/document.pdf"

    # Execute and Assert
    with pytest.raises(MediaProcessingError, match="Unsupported media type"):
        await media_service.download_media(url)


@patch("api.services.media.requests.get")
async def test_download_media_too_large(mock_get, media_service):
    """Test handling of file size limit"""
    # Setup
    response = Mock()
    response.status_code = 200
    response.headers = {
        "content-type": "image/jpeg",
        "content-length": str(20 * 1024 * 1024),  # 20MB
    }
    mock_get.return_value = response
    url = "https://example.com/large.jpg"

    # Execute and Assert
    with pytest.raises(MediaProcessingError, match="File size exceeds limit"):
        await media_service.download_media(url)


@patch("api.services.media.requests.get")
async def test_download_video_too_long(
    mock_get, media_service, mock_video_response, mock_ffprobe_result
):
    """Test handling of video duration limit"""
    # Setup
    mock_get.return_value = mock_video_response
    mock_video_response.status_code = 200
    # Create a small test video
    mock_video_response.content = b"test video data"
    mock_video_response.headers = {
        "content-type": "video/mp4",
        "content-length": str(len(mock_video_response.content)),
    }
    url = "https://example.com/long.mp4"
    mock_ffprobe_result["format"]["duration"] = "600"  # 10 minutes
    with patch("ffmpeg.probe") as mock_ffprobe:
        mock_ffprobe.return_value = mock_ffprobe_result

        # Execute and Assert
        with pytest.raises(MediaProcessingError, match="Video duration exceeds limit"):
            await media_service.download_media(url)


@patch("api.services.media.requests.get")
async def test_download_media_network_error(mock_get, media_service):
    """Test handling of network errors"""
    # Setup
    mock_get.side_effect = Exception("Network error")
    url = "https://example.com/image.jpg"

    # Execute and Assert
    with pytest.raises(MediaProcessingError, match="Failed to download media"):
        await media_service.download_media(url)


async def test_store_media_success(media_service, mock_storage):
    """Test successful media storage"""
    # Setup
    media_data = b"test image data"
    media_type = "image/jpeg"
    url = "https://example.com/image.jpg"
    mock_storage.upload.return_value = "https://cdn.example.com/image.jpg"

    # Execute
    stored_url = await media_service.store_media(media_data, media_type, url)

    # Assert
    assert stored_url == "https://cdn.example.com/image.jpg"
    mock_storage.upload.assert_called_once()


async def test_store_media_error(media_service, mock_storage):
    """Test handling of storage errors"""
    # Setup
    media_data = b"test image data"
    media_type = "image/jpeg"
    url = "https://example.com/image.jpg"
    mock_storage.upload.side_effect = Exception("Storage error")

    # Execute and Assert
    with pytest.raises(MediaProcessingError, match="Failed to store media"):
        await media_service.store_media(media_data, media_type, url)


async def test_cache_hit(media_service, mock_cache):
    """Test cache hit"""
    # Setup
    url = "https://example.com/image.jpg"
    cached_data = {
        "type": "image",
        "url": "https://cdn.example.com/image.jpg",
        "metadata": {
            "width": 800,
            "height": 600,
            "size_bytes": 1024,
            "format": "jpeg",
            "priority": 80,
            "duration_seconds": None,
        },
    }
    mock_cache.get.return_value = json.dumps(cached_data)

    # Execute
    result = await media_service.get_cached_media(url)

    # Assert
    assert isinstance(result, MediaAsset)
    assert result.type == cached_data["type"]
    assert str(result.url) == cached_data["url"]
    assert result.metadata.format == cached_data["metadata"]["format"]
    assert result.metadata.size_bytes == cached_data["metadata"]["size_bytes"]
    mock_cache.get.assert_called_once_with(url)


async def test_cache_miss(media_service, mock_cache):
    """Test cache miss"""
    # Setup
    url = "https://example.com/image.jpg"
    mock_cache.get.return_value = None

    # Execute
    result = await media_service.get_cached_media(url)

    # Assert
    assert result is None
    mock_cache.get.assert_called_once_with(url)


async def test_update_cache(media_service, mock_cache):
    """Test cache update"""
    # Setup
    url = "https://example.com/image.jpg"
    media_asset = MediaAsset(
        type="image",
        url="https://cdn.example.com/image.jpg",
        metadata=MediaMetadata(
            width=800,
            height=600,
            size_bytes=1024,
            format="jpeg",
            priority=80,
            duration_seconds=None,
        ),
    )

    # Execute
    await media_service.update_cache(url, media_asset)

    # Assert
    mock_cache.set.assert_called_once_with(
        url,
        json.dumps(
            {
                "type": media_asset.type,
                "url": str(media_asset.url),
                "metadata": media_asset.metadata.model_dump(),
            }
        ),
        ttl_seconds=3600,
    )
