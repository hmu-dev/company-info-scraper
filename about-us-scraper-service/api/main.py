from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from api.middleware.rate_limit import setup_rate_limiting
from api.middleware.validation import setup_validation
from api.middleware.compression import setup_compression
from api.middleware.tracing import setup_tracing
from api.utils.versioning import setup_versioning
from api.endpoints import media, profile
import os

app = FastAPI(
    title="AI Web Scraper API",
    description="""
    Extract company information and media from websites using AI.
    
    ## Features
    
    - **Company Profile Extraction**: Extract structured company information including about us, culture, team, and locations
    - **Media Processing**: Download and process images and videos with metadata
    - **Caching**: DynamoDB-based caching for improved performance
    - **Rate Limiting**: Protect API from abuse
    - **Compression**: Automatic response compression
    - **Versioning**: API versioning with deprecation notices
    
    ## Authentication
    
    The API uses API key authentication. Include your API key in the `X-API-Key` header.
    
    ## Rate Limits
    
    - 60 requests per minute per API key
    - Burst limit of 10 requests
    
    ## Media Limits
    
    - Maximum file size: 10MB
    - Maximum video duration: 5 minutes
    - Supported image formats: JPEG, PNG, GIF, WebP, SVG
    - Supported video formats: MP4, WebM
    
    ## Error Handling
    
    The API uses standard HTTP status codes:
    
    - 200: Success
    - 400: Bad Request
    - 401: Unauthorized
    - 429: Too Many Requests
    - 500: Internal Server Error
    
    Error responses include:
    ```json
    {
        "success": false,
        "error": "Error message",
        "error_type": "ErrorType"
    }
    ```
    
    ## Versioning
    
    Include the version in the URL path: `/v1/media`, `/v1/profile`
    
    Version headers in responses:
    - `X-API-Version`: Current version
    - `X-API-Latest-Version`: Latest available version
    - `Warning`: Deprecation notices
    
    ## Compression
    
    The API supports multiple compression formats:
    - `br` (Brotli)
    - `gzip`
    - `deflate`
    
    Include `Accept-Encoding` header to specify preferred formats.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    openapi_tags=[
        {"name": "media", "description": "Media extraction and processing endpoints"},
        {"name": "profile", "description": "Company profile extraction endpoints"},
        {"name": "health", "description": "Health check endpoints"},
    ],
    license_info={"name": "MIT", "url": "https://opensource.org/licenses/MIT"},
    contact={
        "name": "API Support",
        "email": "support@example.com",
        "url": "https://example.com/support",
    },
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up compression
setup_compression(
    app,
    minimum_size=int(os.getenv("COMPRESSION_MIN_SIZE", "1000")),
    compression_level=int(os.getenv("COMPRESSION_LEVEL", "6")),
    excluded_paths=["/health", "/metrics"],
    excluded_types=[
        "image/",
        "video/",
        "audio/",
        "application/zip",
        "application/x-gzip",
        "application/x-brotli",
        "application/x-rar",
    ],
)

# Set up tracing (first to capture all requests)
setup_tracing(app)

# Set up validation
setup_validation(
    app,
    max_url_length=int(os.getenv("MAX_URL_LENGTH", "2048")),
    allowed_schemes=["http", "https"],
    blocked_domains=os.getenv("BLOCKED_DOMAINS", "").split(","),
    max_content_length=int(os.getenv("MAX_CONTENT_LENGTH", "10485760")),  # 10MB
)

# Set up rate limiting
setup_rate_limiting(
    app,
    requests_per_minute=int(os.getenv("RATE_LIMIT_RPM", "60")),
    burst_limit=int(os.getenv("RATE_LIMIT_BURST", "10")),
    exclude_paths=["/health", "/metrics"],
    key_func=lambda request: request.headers.get("X-API-Key", request.client.host),
)

# Set up versioning
version_manager = setup_versioning(
    app,
    current_version=os.getenv("API_VERSION", "1.0.0"),
    min_version=os.getenv("API_MIN_VERSION", "1.0.0"),
    max_version=os.getenv("API_MAX_VERSION", "2.0.0"),
)

# Include routers
app.include_router(media.router, prefix="/v1", tags=["media"])
app.include_router(profile.router, prefix="/v1", tags=["profile"])


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return {"metrics": "Coming soon"}
