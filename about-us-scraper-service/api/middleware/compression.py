from fastapi import Request, Response
from typing import Optional, Dict, List
import gzip
import brotli
import zlib
import io
from ..utils.logging import log_event

class CompressionMiddleware:
    def __init__(self,
                 app,
                 minimum_size: int = 1000,
                 compression_level: int = 6,
                 excluded_paths: Optional[List[str]] = None,
                 excluded_types: Optional[List[str]] = None):
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
            'image/', 'video/', 'audio/',
            'application/zip', 'application/x-gzip',
            'application/x-brotli', 'application/x-rar'
        ]
    
    def should_compress(self, 
                       request: Request,
                       response: Response,
                       content_length: int) -> bool:
        """Check if response should be compressed"""
        # Check if compression is supported
        if 'accept-encoding' not in request.headers:
            return False

        # Check content length
        if content_length < self.minimum_size:
            return False
        
        # Check path exclusions
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return False
        
        # Check content type exclusions
        content_type = response.headers.get('content-type', '')
        if any(t in content_type.lower() for t in self.excluded_types):
            return False
        
        # Check if already compressed
        content_encoding = response.headers.get('content-encoding', '')
        if content_encoding:
            return False
        
        return True
    
    def get_accepted_encodings(self, headers: Dict[str, str]) -> Dict[str, float]:
        """Parse Accept-Encoding header"""
        # Return empty dict if no Accept-Encoding header
        if 'accept-encoding' not in headers:
            return {}

        accept_encoding = headers['accept-encoding'].strip()
        if not accept_encoding:
            return {}

        encodings = {}
        
        # Parse each encoding and its quality value
        for encoding in accept_encoding.split(','):
            encoding = encoding.strip().lower()
            if not encoding:
                continue
            
            # Skip identity encoding
            if encoding == 'identity':
                continue
            
            # Handle quality value
            if ';q=' in encoding:
                encoding, q = encoding.split(';q=')
                try:
                    q = float(q)
                    if q <= 0:  # Skip encodings with q=0
                        continue
                    encodings[encoding] = min(1.0, max(0.0, q))
                except ValueError:
                    continue
            else:
                encodings[encoding] = 1.0
            
            # Handle wildcard
            if encoding == '*':
                # If * is present with q>0, add all supported encodings
                if encodings.get('*', 0) > 0:
                    for enc in ['br', 'gzip', 'deflate']:
                        if enc not in encodings:
                            encodings[enc] = encodings['*']
                del encodings['*']
                continue
            
            # Handle specific encodings
            if encoding in ['br', 'gzip', 'deflate']:
                encodings[encoding] = encodings.get(encoding, 1.0)
        
        # Only keep supported encodings
        supported = {'br', 'gzip', 'deflate'}
        encodings = {k: v for k, v in encodings.items() if k in supported}
        
        return encodings
    
    def compress_content(self, content: bytes, encoding: str) -> Optional[bytes]:
        """Compress content using specified encoding"""
        try:
            if encoding == 'br':
                # Use brotli with text mode for JSON content
                compressed = brotli.compress(
                    content,
                    quality=min(11, self.compression_level),  # Brotli quality is 0-11
                    mode=brotli.MODE_TEXT
                )
                # Verify compression
                try:
                    decompressed = brotli.decompress(compressed)
                    if decompressed == content:
                        return compressed
                except Exception as e:
                    log_event("compression_error", {
                        "encoding": encoding,
                        "error": f"Brotli verification failed: {str(e)}"
                    })
                    return None
            elif encoding == 'gzip':
                # Use gzip.compress for proper gzip format
                compressed = gzip.compress(content, compresslevel=self.compression_level)
                # Verify compression
                try:
                    decompressed = gzip.decompress(compressed)
                    if decompressed == content:
                        return compressed
                except Exception as e:
                    log_event("compression_error", {
                        "encoding": encoding,
                        "error": f"Gzip verification failed: {str(e)}"
                    })
                    return None
            elif encoding == 'deflate':
                # Use standard deflate format (RFC 1950)
                compressed = zlib.compress(content, level=self.compression_level)
                # Verify compression using standard deflate format
                try:
                    decompressed = zlib.decompress(compressed)
                    if decompressed == content:
                        return compressed
                except Exception as e:
                    log_event("compression_error", {
                        "encoding": encoding,
                        "error": f"Deflate verification failed: {str(e)}"
                    })
                    return None
        except Exception as e:
            log_event("compression_error", {
                "encoding": encoding,
                "error": f"Compression failed: {str(e)}"
            })
            return None
        
        return None
    
    async def __call__(self, scope, receive, send):
        """Process request with compression"""
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)

        # Create a new send function to intercept the response
        response_started = False
        response_body = []
        response_headers = {}
        response_status = 200  # Default status code

        async def send_wrapper(message):
            nonlocal response_started, response_body, response_headers, response_status

            if message["type"] == "http.response.start":
                # Store headers and status for later use
                response_headers = {
                    k.decode("latin-1") if isinstance(k, bytes) else k:
                    v.decode("latin-1") if isinstance(v, bytes) else v
                    for k, v in message.get("headers", [])
                }
                response_status = message.get("status", 200)
                
                # For streaming responses, send start message immediately
                if any(h.lower() == "transfer-encoding" and v.lower() == "chunked" 
                      for h, v in response_headers.items()):
                    await send(message)
                    response_started = True
                # Otherwise, wait for body to decide on compression
            
            elif message["type"] == "http.response.body":
                body = message.get("body", b"")
                more_body = message.get("more_body", False)

                # For streaming responses, send each chunk as is
                if more_body:
                    # Send start message if not sent yet
                    if not response_started:
                        await send({
                            "type": "http.response.start",
                            "status": response_status,
                            "headers": [(k.encode("latin-1") if isinstance(k, str) else k,
                                       v.encode("latin-1") if isinstance(v, str) else v)
                                      for k, v in response_headers.items()]
                        })
                        response_started = True
                    await send(message)
                    return

                # For non-streaming responses, collect the body and compress if possible
                response_body.append(body)
                if not more_body:
                    # Get full response body
                    content = b"".join(response_body)
                    content_length = len(content)

                    # Check if compression is needed
                    if not self.should_compress(request, Response(content=content, headers=response_headers), content_length):
                        # Send original response without compression
                        if not response_started:
                            await send({
                                "type": "http.response.start",
                                "status": response_status,
                                "headers": [(k.encode("latin-1") if isinstance(k, str) else k,
                                           v.encode("latin-1") if isinstance(v, str) else v)
                                          for k, v in response_headers.items()]
                            })
                            response_started = True
                        await send({
                            "type": "http.response.body",
                            "body": content,
                            "more_body": False
                        })
                        return

                    # Get accepted encodings
                    encodings = self.get_accepted_encodings(request.headers)
                    if not encodings:
                        # Send original response without compression
                        if not response_started:
                            await send({
                                "type": "http.response.start",
                                "status": response_status,
                                "headers": [(k.encode("latin-1") if isinstance(k, str) else k,
                                           v.encode("latin-1") if isinstance(v, str) else v)
                                          for k, v in response_headers.items()]
                            })
                            response_started = True
                        await send(message)
                        return

                    # Try compression methods in order of preference
                    # Sort by quality value
                    preferred_encodings = sorted(
                        [(enc, encodings[enc]) for enc in ['br', 'gzip', 'deflate'] if enc in encodings],
                        key=lambda x: x[1],
                        reverse=True
                    )

                    for encoding, _ in preferred_encodings:
                        try:
                            compressed = self.compress_content(content, encoding)
                            if compressed:
                                # Compression was successful and verified

                                # Log compression stats
                                compression_ratio = len(compressed) / content_length
                                log_event("compression_applied", {
                                    "encoding": encoding,
                                    "original_size": content_length,
                                    "compressed_size": len(compressed),
                                    "ratio": compression_ratio
                                })

                                # Update response headers
                                headers = [
                                    (b"content-encoding", encoding.encode()),
                                    (b"content-length", str(len(compressed)).encode()),
                                    *[(k.encode("latin-1") if isinstance(k, str) else k,
                                       v.encode("latin-1") if isinstance(v, str) else v)
                                      for k, v in response_headers.items()
                                      if k.lower() not in ["content-encoding", "content-length"]]
                                ]

                                # Send response with updated headers
                                if not response_started:
                                    await send({
                                        "type": "http.response.start",
                                        "status": response_status,
                                        "headers": headers
                                    })
                                    response_started = True
                                await send({
                                    "type": "http.response.body",
                                    "body": compressed,
                                    "more_body": False
                                })
                                return
                        except Exception as e:
                            log_event("compression_error", {
                                "encoding": encoding,
                                "error": str(e)
                            })
                            continue

                    # If no compression was possible, send original response
                    if not response_started:
                        await send({
                            "type": "http.response.start",
                            "status": response_status,
                            "headers": [(k.encode("latin-1") if isinstance(k, str) else k,
                                       v.encode("latin-1") if isinstance(v, str) else v)
                                      for k, v in response_headers.items()]
                        })
                        response_started = True
                    await send(message)

        await self.app(scope, receive, send_wrapper)

def setup_compression(
    app,
    minimum_size: int = 1000,
    compression_level: int = 6,
    excluded_paths: Optional[List[str]] = None,
    excluded_types: Optional[List[str]] = None
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
        excluded_types=excluded_types
    )
