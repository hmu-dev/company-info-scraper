from fastapi import Request, Response
from typing import Optional, Dict, List
import gzip
import brotli
import zlib
from ..utils.logging import log_event


class CompressionMiddleware:
    def __init__(
        self,
        app,
        minimum_size: int = 1000,
        compression_level: int = 6,
        excluded_paths: Optional[List[str]] = None,
        excluded_types: Optional[List[str]] = None,
    ):
        """
        Initialize compression middleware

        Args:
            app: FastAPI application
            minimum_size: Minimum response size to compress
            compression_level: Compression level (1-9)
            excluded_paths: List of paths to exclude from compression
            excluded_types: List of content types to exclude from compression
        """
        self.app = app
        self.minimum_size = minimum_size
        self.compression_level = compression_level
        self.excluded_paths = excluded_paths or []
        self.excluded_types = excluded_types or [
            "image/",
            "video/",
            "audio/",
            "application/zip",
            "application/x-gzip",
            "application/x-brotli",
            "application/x-rar",
        ]

    def should_compress(
        self, request: Request, response: Response, content_length: int
    ) -> bool:
        """Check if response should be compressed"""
        # Check content length
        if content_length < self.minimum_size:
            return False

        # Check path exclusions
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return False

        # Check content type exclusions
        content_type = response.headers.get("content-type", "")
        if any(t in content_type.lower() for t in self.excluded_types):
            return False

        # Check if already compressed
        content_encoding = response.headers.get("content-encoding", "")
        if content_encoding:
            return False

        return True

    def get_accepted_encodings(self, request: Request) -> Dict[str, float]:
        """Parse Accept-Encoding header"""
        accept_encoding = request.headers.get("accept-encoding", "")
        encodings = {}

        if not accept_encoding:
            return encodings

        for encoding in accept_encoding.split(","):
            encoding = encoding.strip()
            if ";q=" in encoding:
                encoding, q = encoding.split(";q=")
                encodings[encoding] = float(q)
            else:
                encodings[encoding] = 1.0

        return encodings

    def compress_content(self, content: bytes, encoding: str) -> Optional[bytes]:
        """Compress content using specified encoding"""
        try:
            if encoding == "br":
                return brotli.compress(content, quality=self.compression_level)
            elif encoding == "gzip":
                return gzip.compress(content, compresslevel=self.compression_level)
            elif encoding == "deflate":
                return zlib.compress(content, level=self.compression_level)
        except Exception as e:
            log_event("compression_error", {"encoding": encoding, "error": str(e)})

        return None

    async def __call__(self, request: Request, call_next):
        """Process request with compression"""
        # Get response
        response = await call_next(request)

        # Get response content
        content = b""
        async for chunk in response.body_iterator:
            content += chunk

        content_length = len(content)

        # Check if should compress
        if not self.should_compress(request, response, content_length):
            return Response(
                content=content,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

        # Get accepted encodings
        encodings = self.get_accepted_encodings(request)

        # Try compression methods in order of preference
        for encoding in ["br", "gzip", "deflate"]:
            if encoding in encodings:
                compressed = self.compress_content(content, encoding)
                if compressed:
                    # Log compression stats
                    compression_ratio = len(compressed) / content_length
                    log_event(
                        "compression_applied",
                        {
                            "encoding": encoding,
                            "original_size": content_length,
                            "compressed_size": len(compressed),
                            "ratio": compression_ratio,
                        },
                    )

                    # Create compressed response
                    headers = dict(response.headers)
                    headers["content-encoding"] = encoding
                    headers["content-length"] = str(len(compressed))
                    headers.pop("transfer-encoding", None)

                    return Response(
                        content=compressed,
                        status_code=response.status_code,
                        headers=headers,
                        media_type=response.media_type,
                    )

        # If no compression was possible, return original response
        return Response(
            content=content,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )


def setup_compression(
    app,
    minimum_size: int = 1000,
    compression_level: int = 6,
    excluded_paths: Optional[List[str]] = None,
    excluded_types: Optional[List[str]] = None,
):
    """
    Set up response compression

    Args:
        app: FastAPI application
        minimum_size: Minimum response size to compress
        compression_level: Compression level (1-9)
        excluded_paths: List of paths to exclude from compression
        excluded_types: List of content types to exclude from compression
    """
    app.add_middleware(
        CompressionMiddleware,
        minimum_size=minimum_size,
        compression_level=compression_level,
        excluded_paths=excluded_paths,
        excluded_types=excluded_types,
    )
