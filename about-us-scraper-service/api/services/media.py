from typing import TYPE_CHECKING, Any, Dict, Optional, Tuple

if TYPE_CHECKING:
    from ..utils.storage import MediaStorage
    from ..utils.cache import Cache

import asyncio
import hashlib
import json
import mimetypes
import os
from io import BytesIO

import aiohttp
import cairosvg
import ffmpeg
import requests
from PIL import Image

from ..models import MediaAsset, MediaMetadata
from ..utils.logging import log_event
from ..utils.retry import MediaProcessingError, retryable


class MediaService:
    def __init__(
        self,
        storage: "MediaStorage",
        cache: "Cache",
        max_file_size: int = 10 * 1024 * 1024,  # 10MB
        max_video_duration: int = 300,  # 5 minutes
        supported_image_types: Optional[list] = None,
        supported_video_types: Optional[list] = None,
    ):
        """Initialize media service

        Args:
            storage: MediaStorage instance for storing media files
            cache: Cache instance for caching media metadata
            max_file_size: Maximum allowed file size in bytes
            max_video_duration: Maximum allowed video duration in seconds
            supported_image_types: List of supported image MIME types
            supported_video_types: List of supported video MIME types
        """
        self.storage = storage
        self.cache = cache
        self.max_size = max_file_size
        self.max_video_duration = max_video_duration
        self.allowed_image_types = supported_image_types or [
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/webp",
            "image/svg+xml",
        ]
        self.allowed_video_types = supported_video_types or ["video/mp4", "video/webm"]

    @retryable(
        max_attempts=3,
        initial_delay=1.0,
        max_delay=10.0,
        exponential_base=2.0,
        jitter=True,
    )
    async def download_media(self, url: str) -> MediaAsset:
        """
        Download media from URL

        Args:
            url: Media URL

        Returns:
            MediaAsset object

        Raises:
            MediaProcessingError: If download fails
        """
        # Check cache first
        cached = await self.get_cached_media(url)
        if cached:
            return cached

        try:
            # Download media
            response = requests.get(url, timeout=30)

            # Check status
            if response.status_code != 200:
                raise MediaProcessingError(
                    f"Download failed with status {response.status_code}"
                )

            # Check content type
            content_type = response.headers.get("content-type", "").lower()
            if not any(
                t in content_type
                for t in self.allowed_image_types + self.allowed_video_types
            ):
                raise MediaProcessingError(f"Unsupported media type: {content_type}")

            # Check size
            content_length = int(response.headers.get("content-length", 0))
            if content_length > self.max_size:
                raise MediaProcessingError(
                    f"File size exceeds limit: {content_length} bytes"
                )

            # Process media
            content = response.content
            media_type = (
                "image"
                if any(t in content_type for t in self.allowed_image_types)
                else "video"
            )

            # Process based on type
            if media_type == "image":
                _, metadata = await self.process_image(content, content_type)
            else:
                _, metadata = await self.process_video(content, content_type)

            # Store media
            stored_url = await self.store_media(content, content_type, url)

            # Create asset
            media_asset = MediaAsset(
                type=media_type,
                url=url,
                metadata=MediaMetadata(
                    width=metadata.get("width", 800),
                    height=metadata.get("height", 600),
                    size_bytes=metadata.get("size_bytes", content_length),
                    format=metadata.get("format", content_type.split("/")[-1]),
                    priority=80,  # Default priority (0-100)
                    duration_seconds=metadata.get("duration_seconds"),
                ),
                context=metadata.get("context", f"{media_type.title()} from {url}"),
            )

            # Cache asset
            await self.update_cache(url, media_asset)

            return media_asset

        except requests.RequestException as e:
            raise MediaProcessingError(f"Failed to download media: {str(e)}")
        except Exception as e:
            raise MediaProcessingError(f"Failed to download media: {str(e)}")

    @retryable(
        max_attempts=2,
        initial_delay=1.0,
        max_delay=5.0,
        exponential_base=2.0,
        jitter=True,
    )
    async def process_image(
        self, content: bytes, content_type: str
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Process image content

        Args:
            content: Image content
            content_type: Content type

        Returns:
            Tuple of (processed_content, metadata)

        Raises:
            MediaProcessingError: If processing fails
        """
        try:
            # Handle SVG
            if "svg" in content_type:
                # Convert to PNG
                png_content = cairosvg.svg2png(bytestring=content)
                content = png_content
                content_type = "image/png"

            # Open image
            img = Image.open(BytesIO(content))

            # Get metadata
            metadata = {
                "width": img.width,
                "height": img.height,
                "format": img.format.lower(),
                "mode": img.mode,
                "size_bytes": len(content),
            }

            # Log success
            log_event(
                "image_processed", {"content_type": content_type, "metadata": metadata}
            )

            return content, metadata

        except Exception as e:
            raise MediaProcessingError(f"Image processing failed: {str(e)}")

    @retryable(
        max_attempts=2,
        initial_delay=1.0,
        max_delay=5.0,
        exponential_base=2.0,
        jitter=True,
    )
    async def process_video(
        self, content: bytes, content_type: str
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Process video content

        Args:
            content: Video content
            content_type: Content type

        Returns:
            Tuple of (processed_content, metadata)

        Raises:
            MediaProcessingError: If processing fails
        """
        try:
            # Save temporarily
            temp_path = f"temp_{hashlib.md5(content).hexdigest()}.mp4"
            with open(temp_path, "wb") as f:
                f.write(content)

            try:
                # Get video info
                try:
                    probe = ffmpeg.probe(temp_path)
                    video_info = next(
                        s for s in probe["streams"] if s["codec_type"] == "video"
                    )

                    # Check duration
                    duration = float(probe["format"]["duration"])
                    if duration > self.max_video_duration:
                        raise MediaProcessingError(
                            f"Video duration exceeds limit: {duration} seconds"
                        )
                except ffmpeg.Error as e:
                    raise MediaProcessingError(f"Failed to probe video file: {str(e)}")
                except (KeyError, IndexError, ValueError, StopIteration) as e:
                    raise MediaProcessingError(
                        f"Failed to extract video duration: {str(e)}"
                    )

                # Get metadata
                metadata = {
                    "width": int(video_info["width"]),
                    "height": int(video_info["height"]),
                    "size_bytes": len(content),
                    "format": content_type.split("/")[-1],
                    "duration_seconds": duration,
                }

                # Log success
                log_event(
                    "video_processed",
                    {"content_type": content_type, "metadata": metadata},
                )

                return content, metadata

            finally:
                # Clean up temp file
                if os.path.exists(temp_path):
                    os.remove(temp_path)

        except Exception as e:
            raise MediaProcessingError(f"Video processing failed: {str(e)}")

    async def process_media(self, url: str) -> Tuple[bytes, Dict[str, Any]]:
        """
        Download and process media

        Args:
            url: Media URL

        Returns:
            Tuple of (processed_content, metadata)

        Raises:
            MediaProcessingError: If processing fails
        """
        # Download media
        content, content_type = await self.download_media(url)

        # Process based on type
        if any(t in content_type.lower() for t in self.allowed_image_types):
            return await self.process_image(content, content_type)
        elif any(t in content_type.lower() for t in self.allowed_video_types):
            return await self.process_video(content, content_type)
        else:
            raise MediaProcessingError(f"Unsupported content type: {content_type}")

    async def get_cached_media(self, url: str) -> Optional[MediaAsset]:
        """
        Get media asset from cache

        Args:
            url: Media URL

        Returns:
            MediaAsset if found in cache, None otherwise
        """
        try:
            cached_data = await self.cache.get(url)
            if cached_data:
                data = json.loads(cached_data)
                return MediaAsset(
                    type=data["type"],
                    url=data["url"],
                    metadata=MediaMetadata(**data["metadata"]),
                    context=data.get(
                        "context", f"{data['type'].title()} from {data['url']}"
                    ),
                )
            return None
        except Exception as e:
            log_event("cache_error", {"error": str(e)})
            return None

    async def update_cache(
        self, url: str, media_asset: MediaAsset, ttl_seconds: int = 3600
    ) -> None:
        """
        Update media asset in cache

        Args:
            url: Media URL
            media_asset: Media asset to cache
            ttl_seconds: Cache TTL in seconds
        """
        try:
            await self.cache.set(
                url,
                json.dumps(
                    {
                        "type": media_asset.type,
                        "url": str(media_asset.url),
                        "metadata": media_asset.metadata.model_dump(),
                    }
                ),
                ttl_seconds=ttl_seconds,
            )
        except Exception as e:
            log_event("cache_error", {"error": str(e)})

    async def store_media(self, media_data: bytes, media_type: str, url: str) -> str:
        """
        Store media data in storage

        Args:
            media_data: Media content
            media_type: Media MIME type
            url: Original media URL

        Returns:
            Stored media URL

        Raises:
            MediaProcessingError: If storage fails
        """
        try:
            # Generate filename from URL
            ext = mimetypes.guess_extension(media_type) or ".bin"
            filename = f"{hashlib.md5(url.encode()).hexdigest()}{ext}"

            # Store in S3
            stored_url = await self.storage.upload(filename, media_data, media_type)

            return stored_url

        except Exception as e:
            raise MediaProcessingError(f"Failed to store media: {str(e)}")
