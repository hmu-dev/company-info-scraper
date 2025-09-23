from fastapi import APIRouter, HTTPException, Response
from typing import List, Optional
from ..models import ScrapeRequest, ProfileResponse
from ..services.llm import LLMService
from ..utils.logging import log_event
import time

router = APIRouter()


@router.post(
    "/profile",
    response_model=ProfileResponse,
    summary="Extract company profile",
    description="""
    Extract structured company information from a website.
    
    This endpoint will:
    1. Automatically find the best About/Company page
    2. Extract structured company information using AI
    3. Return profile data in the new 5-section format
    
    This is the faster endpoint, suitable for initial loading in mobile apps.
    
    The response includes five sections:
    - About Us: Company overview and mission
    - Our Culture: Company values and environment
    - Our Team: Key team members and roles
    - Noteworthy & Differentiated: Unique features and achievements
    - Locations: Physical locations (if available)
    
    Example request:
    ```json
    {
        "url": "https://example.com",
        "model": "gpt-3.5-turbo"
    }
    ```
    
    Example response:
    ```json
    {
        "success": true,
        "url_scraped": "https://example.com/about",
        "profile": {
            "about_us": "Example Company is a leading provider...",
            "our_culture": "We believe in innovation and collaboration...",
            "our_team": "Led by CEO Jane Smith...",
            "noteworthy_and_differentiated": "Award-winning technology...",
            "locations": "Headquarters in San Francisco, CA"
        }
    }
    ```
    """,
    responses={
        200: {
            "description": "Successfully extracted profile",
            "headers": {
                "X-API-Version": {
                    "description": "Current API version",
                    "schema": {"type": "string"},
                }
            },
        },
        400: {
            "description": "Invalid request",
            "content": {
                "application/json": {
                    "example": {
                        "success": False,
                        "error": "Invalid URL format",
                        "error_type": "ValidationError",
                    }
                }
            },
        },
        429: {
            "description": "Too many requests",
            "headers": {
                "Retry-After": {
                    "description": "Seconds to wait before retrying",
                    "schema": {"type": "integer"},
                }
            },
        },
    },
)
async def scrape_profile(request: ScrapeRequest) -> ProfileResponse:
    """Extract company profile from website"""
    try:
        start_time = time.time()
        url = str(request.url)

        # Initialize LLM service
        llm = LLMService(api_key=request.openai_api_key, model=request.model)

        # Extract profile
        profile = await llm.extract_content(text=url, prompt=default_prompt)

        # Log success
        duration = time.time() - start_time
        log_event(
            "profile_scrape_success",
            {"url": url, "duration": duration, "model": request.model},
        )

        return ProfileResponse(success=True, url_scraped=url, profile=profile)

    except Exception as e:
        # Log error
        log_event(
            "profile_scrape_error",
            {"url": url, "error": str(e), "error_type": type(e).__name__},
        )

        raise HTTPException(
            status_code=500, detail={"error": str(e), "error_type": type(e).__name__}
        )
