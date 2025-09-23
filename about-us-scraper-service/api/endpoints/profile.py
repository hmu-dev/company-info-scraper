import time
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Response

from ..models import ProfileResponse, ScrapeRequest
from ..services.llm import LLMService
from ..utils.logging import log_event

router = APIRouter()

default_prompt = """Output ONLY valid JSON. Do not include any additional text, explanations, wrappers, or invalid formats—ensure the JSON is parseable without errors. Extract or infer company information into five distinct sections. For all sections EXCEPT locations, if exact information cannot be found, infer positive, professional descriptions based on available website content. For the locations section, only include factual location information—if none found, use "No location found".

The response must be a JSON object with these exact keys:
{
    "about_us": "Company overview and mission",
    "our_culture": "Company values and environment",
    "our_team": "Key team members and roles",
    "noteworthy_and_differentiated": "Unique features and achievements",
    "locations": "Physical locations (if available)"
}

Positive Example 1:
Input: "We are a small bakery in downtown Portland. Our pastry chef trained in Paris."
Output:
{
    "about_us": "A charming artisanal bakery bringing French-inspired pastries to Portland's vibrant downtown scene.",
    "our_culture": "We embrace the dedication to craft and attention to detail that defines French culinary tradition.",
    "our_team": "Led by our Paris-trained pastry chef who brings world-class expertise to every creation.",
    "noteworthy_and_differentiated": "Authentic French pastry techniques combined with local Pacific Northwest ingredients.",
    "locations": "Downtown Portland"
}

Positive Example 2:
Input: "Founded in 2020, we help businesses grow through digital marketing."
Output:
{
    "about_us": "A dynamic digital marketing agency founded in 2020, dedicated to driving business growth through innovative online strategies.",
    "our_culture": "We foster a results-driven environment that embraces creativity and digital innovation.",
    "our_team": "A collaborative group of digital marketing specialists committed to client success.",
    "noteworthy_and_differentiated": "Specialized in creating measurable growth through integrated digital marketing approaches.",
    "locations": "No location found"
}

Negative Example 1:
Input: "Contact us at 555-0123"
Output:
{
    "about_us": "Not available",
    "our_culture": "Not available",
    "our_team": "Not available",
    "noteworthy_and_differentiated": "Not available",
    "locations": "No location found"
}

Remember:
1. ONLY output valid JSON
2. Include ALL five sections
3. Infer positive content for all sections except locations
4. Keep locations factual only
5. Use "No location found" if no location information exists"""


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
        llm = LLMService()

        # Extract profile
        profile = await llm.extract_content(
            text=url, prompt=default_prompt, temperature=0.7
        )

        # Log success
        duration = time.time() - start_time
        log_event(
            "profile_scrape_success",
            {"url": url, "duration": duration, "model": request.model},
        )

        return ProfileResponse(
            success=True,
            duration=duration,
            data=profile,
            token_usage={
                "prompt_tokens": 0,  # TODO: Get from LLM service
                "completion_tokens": 0,  # TODO: Get from LLM service
            },
        )

    except Exception as e:
        # Log error
        log_event(
            "profile_scrape_error",
            {"url": url, "error": str(e), "error_type": type(e).__name__},
        )

        raise HTTPException(
            status_code=500, detail={"error": str(e), "error_type": type(e).__name__}
        )
