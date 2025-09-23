from fastapi import APIRouter, HTTPException, Response
from typing import List, Optional
from ..models import ScrapeRequest, MediaResponse, MediaAsset, MediaMetadata
from ..utils.storage import MediaStorage, StorageError
from ..utils.pagination import paginate_items
from ..utils.logging import log_event
from ..services.html_parser import extract_media_from_html
import time
import os

router = APIRouter()

@router.post(
    "/media",
    response_model=MediaResponse,
    summary="Extract media from website",
    description="""
    Extract and process media content from a website.
    
    This endpoint will:
    1. Extract media from HTML and AI analysis
    2. Process and store media files
    3. Return paginated results with metadata
    4. Support cursor-based pagination
    
    Cache headers are included for efficient mobile app usage.
    
    The response includes:
    - Media items sorted by priority (logos first)
    - Metadata (dimensions, size, format)
    - Pagination information
    - Optional base64 data
    
    Example request:
    ```json
    {
        "url": "https://example.com",
        "include_base64": false,
        "cursor": "next_page_token",
        "limit": 10
    }
    ```
    
    Example response:
    ```json
    {
        "success": true,
        "url_scraped": "https://example.com",
        "media": [
            {
                "url": "https://example.com/logo.png",
                "type": "image",
                "context": "Company logo",
                "metadata": {
                    "width": 200,
                    "height": 100,
                    "size_bytes": 15000,
                    "format": "png"
                },
                "filename": "logo.png",
                "priority": 100
            }
        ],
        "pagination": {
            "total_count": 15,
            "remaining_count": 5,
            "has_more": true,
            "next_cursor": "next_page_token"
        }
    }
    ```
    """,
    responses={
        200: {
            "description": "Successfully extracted media",
            "headers": {
                "X-API-Version": {
                    "description": "Current API version",
                    "schema": {"type": "string"}
                },
                "Cache-Control": {
                    "description": "Caching directives",
                    "schema": {"type": "string"}
                }
            }
        },
        400: {
            "description": "Invalid request",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": "Invalid URL format",
                        "error_type": "ValidationError"
                    }
                }
            }
        },
        429: {
            "description": "Too many requests",
            "headers": {
                "Retry-After": {
                    "description": "Seconds to wait before retrying",
                    "schema": {"type": "integer"}
                }
            }
        }
    }
)
async def scrape_media(request: ScrapeRequest, response: Response):
    """
    Scrape media content from a website with pagination support
    
    This endpoint will:
    1. Extract media from HTML and AI analysis
    2. Process and store media files
    3. Return paginated results with metadata
    4. Support cursor-based pagination
    
    Cache headers are included for efficient mobile app usage.
    """
    try:
        start_time = time.time()
        url = str(request.url).rstrip('/')
        
        # Initialize storage
        storage = MediaStorage(
            bucket_name=os.getenv("S3_BUCKET_NAME"),
            cloudfront_domain=os.getenv("CLOUDFRONT_DOMAIN")
        )
        
        # Extract and process media
        media_items: List[MediaAsset] = []
        
        # Extract from HTML
        html_media = extract_media_from_html(url)
        
        # Process media items
        seen_urls = set()
        for media_url, media_type, context in html_media:
            if media_url not in seen_urls:
                seen_urls.add(media_url)
                
                try:
                    # Download and process media
                    result = await storage.store_media(
                        url=media_url,
                        media_type=media_type
                    )
                    cdn_url, metadata = result
                    
                    # Create media item
                    priority = calculate_priority(context, metadata)
                    media_item = MediaAsset(
                        url=cdn_url,
                        type=media_type,
                        context=context,
                        metadata=MediaMetadata(
                            width=metadata.get('width'),
                            height=metadata.get('height'),
                            size_bytes=metadata['size_bytes'],
                            format=metadata['format'],
                            priority=priority,
                            duration_seconds=metadata.get('duration_seconds')
                        )
                    )
                    
                    media_items.append(media_item)
                    
                except Exception as e:
                    log_event("media_processing_error", {
                        "url": media_url,
                        "error": str(e)
                    })
                    # Re-raise storage errors to trigger 500 response
                    if isinstance(e, StorageError):
                        log_event("media_scrape_error", {
                            "url": url,
                            "error": str(e),
                            "error_type": "StorageError"
                        })
                        raise HTTPException(
                            status_code=500,
                            detail={
                                "error": str(e),
                                "error_type": "StorageError"
                            }
                        ) from e
                    continue
        
        # Sort by priority
        media_items.sort(key=lambda x: x.metadata.priority, reverse=True)
        
        # Apply pagination
        paginated_result = paginate_items(
            items=media_items,
            limit=request.limit or 10,
            cursor=request.cursor
        )
        
        # Add cache headers
        response.headers["Cache-Control"] = "public, max-age=3600"  # 1 hour
        response.headers["Vary"] = "Accept-Encoding"
        
        # Log success
        duration = time.time() - start_time
        log_event("media_scrape_success", {
            "url": url,
            "duration": duration,
            "total_items": len(media_items),
            "returned_items": len(paginated_result.items)
        })
        
        return MediaResponse(
            success=True,
            duration=duration,
            url_scraped=url,
            media=paginated_result.items,
            pagination=paginated_result.pagination
        )
        
    except Exception as e:
        # Log error
        log_event("media_scrape_error", {
            "url": url,
            "error": str(e),
            "error_type": type(e).__name__
        })
        
        raise HTTPException(
            status_code=500,
            detail={
                "error": str(e),
                "error_type": "StorageError" if isinstance(e, StorageError) else type(e).__name__
            }
        )

def calculate_priority(context: str, metadata: dict) -> int:
    """
    Calculate priority score for media item.

    Args:
        context: The context in which the media appears
        metadata: Media metadata including dimensions

    Returns:
        Priority score between 0 and 100
    """
    priority = 10  # default score
    
    # Boost based on context (max 80)
    context_lower = context.lower()
    if any(key in context_lower for key in ['logo', 'brand']):
        priority = 80
    elif any(key in context_lower for key in ['team', 'founder', 'leader']):
        priority = 60
    elif any(key in context_lower for key in ['office', 'location']):
        priority = 40
    elif any(key in context_lower for key in ['product', 'service']):
        priority = 30
    
    # Boost based on metadata (max +20)
    if metadata.get('width') and metadata.get('height'):
        # Boost square-ish images (likely logos)
        aspect_ratio = metadata['width'] / metadata['height']
        if 0.8 <= aspect_ratio <= 1.2:
            priority = min(priority + 15, 100)
            
        # Boost high-resolution images
        if metadata['width'] >= 1000 or metadata['height'] >= 1000:
            priority = min(priority + 5, 100)
    
    return priority
