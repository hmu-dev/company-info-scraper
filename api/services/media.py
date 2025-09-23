from typing import Dict, Any, Optional, Tuple
import aiohttp
import asyncio
import os
import hashlib
import mimetypes
from PIL import Image
from io import BytesIO
import cairosvg
import ffmpeg
from ..utils.retry import retryable, MediaProcessingError
from ..utils.logging import log_event


class MediaService:
    def __init__(
        self,
        max_size: int = 10 * 1024 * 1024,  # 10MB
        max_video_duration: int = 300,  # 5 minutes
        allowed_image_types: Optional[list] = None,
        allowed_video_types: Optional[list] = None,
    ):
        """Initialize media service"""
        self.max_size = max_size
        self.max_video_duration = max_video_duration
        self.allowed_image_types = allowed_image_types or [
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/webp",
            "image/svg+xml",
        ]
        self.allowed_video_types = allowed_video_types or ["video/mp4", "video/webm"]

    @retryable(
        max_attempts=3,
        initial_delay=1.0,
        max_delay=10.0,
        exponential_base=2.0,
        jitter=True,
    )
    async def download_media(self, url: str) -> Tuple[bytes, str]:
        """
        Download media from URL

        Args:
            url: Media URL

        Returns:
            Tuple of (content, content_type)

        Raises:
            MediaProcessingError: If download fails
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    # Check status
                    if response.status != 200:
                        raise MediaProcessingError(
                            f"Download failed with status {response.status}"
                        )

                    # Check content type
                    content_type = response.headers.get("content-type", "")
                    if not any(
                        t in content_type.lower()
                        for t in self.allowed_image_types + self.allowed_video_types
                    ):
                        raise MediaProcessingError(
                            f"Unsupported content type: {content_type}"
                        )

                    # Check content length
                    content_length = int(response.headers.get("content-length", 0))
                    if content_length > self.max_size:
                        raise MediaProcessingError(
                            f"Content too large: {content_length} bytes"
                        )

                    # Download content
                    content = await response.read()

                    return content, content_type

        except aiohttp.ClientError as e:
            raise MediaProcessingError(f"Download failed: {str(e)}")
        except Exception as e:
            raise MediaProcessingError(f"Unexpected error: {str(e)}")

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
                probe = ffmpeg.probe(temp_path)
                video_info = next(
                    s for s in probe["streams"] if s["codec_type"] == "video"
                )

                # Check duration
                duration = float(probe["format"]["duration"])
                if duration > self.max_video_duration:
                    raise MediaProcessingError(f"Video too long: {duration} seconds")

                # Get metadata
                metadata = {
                    "width": int(video_info["width"]),
                    "height": int(video_info["height"]),
                    "duration": duration,
                    "format": content_type.split("/")[-1],
                    "codec": video_info["codec_name"],
                    "size_bytes": len(content),
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
