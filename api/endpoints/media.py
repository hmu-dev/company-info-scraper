from fastapi import APIRouter, HTTPException, Response
from typing import List, Optional
from ..models import ScrapeRequest, MediaResponse, MediaItem
from ..utils.storage import MediaStorage
from ..utils.pagination import paginate_items
from ..utils.logging import log_event
import time

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
        url = str(request.url)
        
        # Initialize storage
        storage = MediaStorage(
            bucket_name=os.getenv("S3_BUCKET_NAME"),
            cloudfront_domain=os.getenv("CLOUDFRONT_DOMAIN")
        )
        
        # Extract and process media
        media_items: List[MediaItem] = []
        
        # Extract from HTML
        html_media = extract_media_from_html(url)
        
        # Process media items
        seen_urls = set()
        for media_url, media_type, context in html_media:
            if media_url not in seen_urls:
                seen_urls.add(media_url)
                
                try:
                    # Download and process media
                    cdn_url, metadata = await storage.store_media(
                        url=media_url,
                        media_type=media_type
                    )
                    
                    # Create media item
                    media_item = MediaItem(
                        url=cdn_url,
                        type=media_type,
                        context=context,
                        metadata=metadata,
                        filename=metadata['filename'],
                        priority=calculate_priority(context, metadata)
                    )
                    
                    media_items.append(media_item)
                    
                except Exception as e:
                    log_event("media_processing_error", {
                        "url": media_url,
                        "error": str(e)
                    })
                    continue
        
        # Sort by priority
        media_items.sort(key=lambda x: x.priority, reverse=True)
        
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
                "error_type": type(e).__name__
            }
        )

def calculate_priority(context: str, metadata: dict) -> int:
    """Calculate priority score for media item"""
    priority = 10  # default score
    
    # Boost based on context
    context_lower = context.lower()
    if any(key in context_lower for key in ['logo', 'brand']):
        priority = 100
    elif any(key in context_lower for key in ['team', 'founder', 'leader']):
        priority = 80
    elif any(key in context_lower for key in ['office', 'location']):
        priority = 60
    elif any(key in context_lower for key in ['product', 'service']):
        priority = 40
    
    # Boost based on metadata
    if metadata.get('width') and metadata.get('height'):
        # Boost square-ish images (likely logos)
        aspect_ratio = metadata['width'] / metadata['height']
        if 0.8 <= aspect_ratio <= 1.2:
            priority += 20
            
        # Boost high-resolution images
        if metadata['width'] >= 1000 or metadata['height'] >= 1000:
            priority += 10
    
    return priority
