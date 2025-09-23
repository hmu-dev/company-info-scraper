# FastAPI-based Web Scraper API
import base64
import json
import os
import re
from io import BytesIO
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI
from PIL import Image
from pydantic import BaseModel, HttpUrl
from scrapegraphai.graphs import SmartScraperGraph

# Default API key - replace with your actual key
DEFAULT_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Default prompt for AI scraping
default_prompt = """Output ONLY valid JSON. Do not include any additional text, explanations, wrappers, or invalid formats—ensure the JSON is parseable without errors. Always include all four profile keys, even if partial or missing (use 'Not available' for missing sections). For media, use an empty array [] if none found.

Positive Example 1 (follow this structure for complete responses):
{'profile': {'About Us (including locations)': 'NEXT Insurance is a company that specializes in providing various types of business insurance, covering a wide range of professions including construction, contractors, consultants, and more. The company is focused on offering coverage for 1,300+ professions and has a mission to recommend the ideal fit for each business. There are physical locations associated with the company in Palo Alto, California.', 'Our Culture': 'NEXT Insurance emphasizes a customer-centric approach, focusing on providing tailored insurance solutions to meet the diverse needs of different professions. The company values innovation, efficiency, and transparency in its operations. The working environment at NEXT Insurance is described as collaborative, empowering, and supportive, fostering growth and development.', 'Our Team': 'Key individuals within NEXT Insurance include the contributing writer Ashley Henshaw, who specializes in small business topics. The company also has a team dedicated to providing expert guidance on licensing requirements, insurance options, and support for professionals in various industries.', 'Noteworthy & Differentiated': 'NEXT Insurance stands out by offering specialized insurance solutions for a wide range of professions, emphasizing the importance of tailored coverage for specific industry needs. The company also provides support for licensing requirements, innovative online services, and a customer-focused approach that sets it apart from traditional insurance providers.'}, 'media': [{'url': 'https://www.nextinsurance.com/wp-content/uploads/2024/08/featured_card_navigation.png', 'type': 'image'}, {'url': 'https://www.nextinsurance.com/wp-content/uploads/2022/04/april-2022-4-802x454.jpg', 'type': 'image'}, {'url': 'https://www.nextinsurance.com/wp-content/uploads/2022/07/Ashley_Henshaw.png', 'type': 'image'}, {'url': 'https://www.nextinsurance.com/wp-content/uploads/2023/11/banner-get-business-insurance-in-10.png', 'type': 'image'}]}

Please extract information from the provided website to create a company profile. Organize the extracted content into the following four distinct sections, ensuring each section is clearly delineated and contains relevant details: About Us (including locations): This section should provide a concise overview of the company, its mission, and its primary activities. Crucially, identify and list all physical locations associated with the company. Our Culture: Describe the core values, working environment, and overall ethos of the company. Look for descriptions of how the company operates, its philosophy, and what it emphasizes in its internal and external interactions. Our Team: Identify key individuals, leadership, or significant roles within the company. If specific team members are highlighted, include their names and relevant contributions or backgrounds. Noteworthy & Differentiated: This section is for unique selling propositions, special features, awards, or any aspects that make the company stand out from its competitors. Look for innovative services, unique offerings, or distinctive operational models. For each section, aim for clear, descriptive language. The overall profile should be comprehensive yet concise, suitable for a mobile app experience. Pay close attention to details that highlight the company's identity and what makes it unique. Keep the response less than 500 words. Additionally, extract any media (videos and images) that are relevant to company branding (i.e. logos, and media about the company). These images will be used to populate an about-us section for the given company in a recruiting app. Respond in strict JSON format with two main keys: 'profile' (an object with the four sections as keys, each containing a string description) and 'media' (an array of objects, each with 'url' and 'type' ('image' or 'video'))."""

app = FastAPI(
    title="AI Web Scraper API",
    description="Extract company information and media from websites using AI",
    version="1.0.0",
)


# Request/Response Models
class ScrapeRequest(BaseModel):
    url: HttpUrl
    openai_api_key: Optional[str] = None  # Optional, will use default if not provided
    model: str = "gpt-3.5-turbo"
    include_base64: bool = False  # Whether to include base64 data in media response


class CompanyProfile(BaseModel):
    about_us: str
    our_culture: str
    our_team: str
    noteworthy_and_differentiated: str
    locations: str


class MediaMetadata(BaseModel):
    width: Optional[int] = None
    height: Optional[int] = None
    size_bytes: Optional[int] = None
    format: Optional[str] = None


class MediaItem(BaseModel):
    url: str
    type: str  # "image" or "video"
    context: str  # e.g., "logo", "team photo", etc.
    metadata: MediaMetadata
    base64_data: Optional[str] = None
    filename: str
    priority: (
        int  # Higher number = more relevant (e.g., logo = 100, general image = 10)
    )


class ProfileResponse(BaseModel):
    success: bool
    url_scraped: str
    profile: CompanyProfile
    error: Optional[str] = None


class MediaResponse(BaseModel):
    success: bool
    url_scraped: str
    media: List[MediaItem]
    error: Optional[str] = None


class CombinedResponse(BaseModel):
    success: bool
    url_scraped: str
    profile: CompanyProfile
    media: List[MediaItem]
    error: Optional[str] = None


# Core scraping functions (adapted from the Streamlit app)
def download_media_to_base64(media_url: str, base_url: str, context: str = "") -> tuple:
    """Download media and extract metadata"""
    try:
        if not media_url.startswith(("http://", "https://")):
            media_url = urljoin(base_url, media_url)

        response = requests.get(media_url, timeout=30, stream=True)

        if response.status_code == 200:
            content = response.content
            content_type = response.headers.get("content-type", "").lower()
            content_length = int(response.headers.get("content-length", 0))

            # Get file info
            parsed_url = urlparse(media_url)
            file_name = os.path.basename(parsed_url.path)

            if not file_name or "." not in file_name:
                if "video" in content_type:
                    file_name = f"video_{hash(media_url) % 10000}.mp4"
                else:
                    file_name = f"image_{hash(media_url) % 10000}.jpg"

            # Determine media type and format
            file_ext = file_name.lower().split(".")[-1]
            media_type = (
                "video"
                if file_ext in ["mp4", "webm", "avi", "mov", "mkv", "flv", "m4v"]
                else "image"
            )

            # Extract metadata
            metadata = MediaMetadata(size_bytes=content_length, format=file_ext)

            # For images, get dimensions
            if media_type == "image":
                try:
                    img = Image.open(BytesIO(content))
                    metadata.width, metadata.height = img.size
                except:
                    pass

            # Calculate priority score based on context and metadata
            priority = 10  # default score

            # Boost score for important contexts
            context_lower = context.lower()
            if any(key in context_lower for key in ["logo", "brand"]):
                priority = 100
            elif any(key in context_lower for key in ["team", "founder", "leader"]):
                priority = 80
            elif any(
                key in context_lower for key in ["office", "location", "building"]
            ):
                priority = 60
            elif any(key in context_lower for key in ["product", "service"]):
                priority = 40

            # Boost score for likely logo dimensions
            if media_type == "image" and metadata.width and metadata.height:
                aspect_ratio = metadata.width / metadata.height
                if (
                    0.8 <= aspect_ratio <= 1.2 and metadata.width >= 100
                ):  # square-ish logos
                    priority += 20

            # Convert to base64 if small enough (skip large files)
            base64_data = None
            if content_length < 5_000_000:  # 5MB limit
                base64_data = base64.b64encode(content).decode("utf-8")

            return (
                media_url,
                media_type,
                base64_data,
                file_name,
                metadata,
                priority,
                context,
            )

    except Exception as e:
        print(f"Could not download media from {media_url}: {str(e)}")

    return None, None, None, None, None, 0, ""


def extract_media_from_html(url: str) -> List[tuple]:
    """Extract media URLs directly from HTML"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            media_urls = []

            # Find images
            img_tags = soup.find_all("img")
            for img in img_tags:
                src = img.get("src") or img.get("data-src") or img.get("data-lazy-src")
                if src:
                    alt_text = (img.get("alt") or "").lower()
                    src_lower = src.lower()

                    # Look for company/branding images
                    if any(
                        keyword in alt_text or keyword in src_lower
                        for keyword in [
                            "logo",
                            "brand",
                            "company",
                            "team",
                            "about",
                            "founder",
                            "staff",
                            "office",
                        ]
                    ):
                        media_urls.append(
                            (
                                src,
                                "image",
                                f"Company image: {alt_text or 'Branding content'}",
                            )
                        )
                    elif not any(
                        ui_element in src_lower
                        for ui_element in [
                            "icon",
                            "button",
                            "arrow",
                            "cart",
                            "search",
                            "menu",
                        ]
                    ):
                        media_urls.append(
                            (
                                src,
                                "image",
                                f"Content image: {alt_text or 'Page content'}",
                            )
                        )

            # Find videos
            video_tags = soup.find_all(["video", "source"])
            for video in video_tags:
                src = video.get("src")
                if src:
                    media_urls.append((src, "video", "Video content"))

            # Find background images in CSS
            style_tags = soup.find_all(["div", "section", "header"], style=True)
            for tag in style_tags:
                style = tag.get("style", "")
                bg_matches = re.findall(
                    r'background-image:\s*url\(["\']?([^"\']+)["\']?\)', style
                )
                for bg_url in bg_matches:
                    media_urls.append((bg_url, "image", "Background image"))

            return media_urls
    except Exception as e:
        print(f"Could not extract media from HTML: {str(e)}")

    return []


def find_about_page(base_url: str) -> str:
    """Find the best About Us page"""
    try:
        parsed_url = urlparse(base_url)
        domain = f"{parsed_url.scheme}://{parsed_url.netloc}"

        # First check if current URL has about content
        try:
            response = requests.get(base_url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, "html.parser")
                page_text = soup.get_text().lower()
                if any(
                    keyword in page_text
                    for keyword in [
                        "about us",
                        "our story",
                        "our team",
                        "our company",
                        "founded",
                    ]
                ):
                    return base_url
        except:
            pass

        # Search for about pages from main domain
        response = requests.get(domain, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")

            about_keywords = [
                "about",
                "about-us",
                "about_us",
                "company",
                "our-story",
                "our-team",
                "team",
                "story",
            ]

            # Look in navigation first
            nav_areas = soup.find_all(["nav", "header", "menu"]) + soup.find_all(
                "ul", class_=re.compile(r"nav|menu", re.I)
            )

            for nav in nav_areas:
                links = nav.find_all("a", href=True)
                for link in links:
                    href = link["href"].lower()
                    link_text = link.get_text().lower().strip()

                    if any(
                        keyword in href or keyword in link_text
                        for keyword in about_keywords
                    ):
                        return urljoin(domain, link["href"])

            # Check common about page paths
            common_paths = [
                "/about",
                "/about-us",
                "/about_us",
                "/company",
                "/our-story",
                "/our-team",
                "/pages/about",
                "/pages/about-us",
                "/about/",
                "/company/",
                "/story/",
            ]

            for path in common_paths:
                test_url = urljoin(domain, path)
                try:
                    test_response = requests.head(test_url, timeout=5)
                    if test_response.status_code == 200:
                        return test_url
                except:
                    continue

    except Exception as e:
        print(f"Could not search for about page: {str(e)}")

    return base_url


def extract_media_from_ai_result(result: Dict[str, Any]) -> List[tuple]:
    """Extract media URLs from AI scraping results"""
    media_urls = []

    def process_content(content, path=""):
        if isinstance(content, dict):
            for key, value in content.items():
                current_path = f"{path}.{key}" if path else key
                if key.lower() in [
                    "image",
                    "img",
                    "logo",
                    "photo",
                    "picture",
                    "icon",
                    "video",
                    "movie",
                    "clip",
                    "media",
                ] and isinstance(value, str):
                    media_extensions = [
                        ".jpg",
                        ".jpeg",
                        ".png",
                        ".gif",
                        ".svg",
                        ".webp",
                        ".mp4",
                        ".webm",
                        ".avi",
                        ".mov",
                        ".mkv",
                        ".flv",
                        ".m4v",
                    ]
                    if any(ext in value.lower() for ext in media_extensions):
                        media_type = (
                            "video"
                            if any(
                                ext in value.lower()
                                for ext in [
                                    ".mp4",
                                    ".webm",
                                    ".avi",
                                    ".mov",
                                    ".mkv",
                                    ".flv",
                                    ".m4v",
                                ]
                            )
                            else "image"
                        )
                        media_urls.append(
                            (value, media_type, f"AI found: {current_path}")
                        )
                elif isinstance(value, (dict, list)):
                    process_content(value, current_path)
        elif isinstance(content, list):
            for i, item in enumerate(content):
                current_path = f"{path}[{i}]"
                process_content(item, current_path)

    if isinstance(result, dict) and "content" in result:
        process_content(result["content"])
    else:
        process_content(result)

    return media_urls


# API Endpoints
@app.post("/scrape/profile", response_model=ProfileResponse)
async def scrape_profile(request: ScrapeRequest):
    """
    Scrape a website for company profile information only.

    This endpoint will:
    1. Automatically find the best About/Company page
    2. Extract structured company information using AI
    3. Return profile data in the new 5-section format

    This is the faster endpoint, suitable for initial loading in mobile apps.
    """
    try:
        url = str(request.url)
        scrape_url = find_about_page(url)

        # Use provided API key or default
        api_key = request.openai_api_key or DEFAULT_OPENAI_API_KEY

        # Set up AI scraper configuration
        graph_config = {
            "llm": {
                "api_key": api_key,
                "model": request.model,
            },
        }

        # Try scraping with AI
        result = None
        urls_to_try = [scrape_url, url] if scrape_url != url else [url]

        for try_url in urls_to_try:
            try:
                smart_scraper_graph = SmartScraperGraph(
                    prompt=default_prompt, source=try_url, config=graph_config
                )

                result = smart_scraper_graph.run()

                if result and isinstance(result, dict):
                    content = result.get("content", {}).get("profile", {})
                    if content and any(content.values()):
                        # Convert to new profile format
                        profile = CompanyProfile(
                            about_us=content.get(
                                "About Us (including locations)", "Not available"
                            ),
                            our_culture=content.get("Our Culture", "Not available"),
                            our_team=content.get("Our Team", "Not available"),
                            noteworthy_and_differentiated=content.get(
                                "Noteworthy & Differentiated", "Not available"
                            ),
                            locations="No location found",  # Default value
                        )

                        # Extract location if present
                        about_us = content.get("About Us (including locations)", "")
                        location_patterns = [
                            r"located\s+(?:in|at)\s+([^\.]+)",
                            r"address[:\s]+([^\.]+)",
                            r"headquarters[:\s]+([^\.]+)",
                            r"based\s+(?:in|at)\s+([^\.]+)",
                        ]

                        for pattern in location_patterns:
                            match = re.search(pattern, about_us, re.IGNORECASE)
                            if match:
                                profile.locations = match.group(1).strip()
                                break

                        return ProfileResponse(
                            success=True, url_scraped=try_url, profile=profile
                        )

            except Exception as e:
                print(f"Error scraping {try_url}: {str(e)}")
                continue

        # If we get here, no successful scrape
        return ProfileResponse(
            success=False,
            url_scraped=url,
            profile=CompanyProfile(
                about_us="Not available",
                our_culture="Not available",
                our_team="Not available",
                noteworthy_and_differentiated="Not available",
                locations="No location found",
            ),
            error="Could not extract profile information",
        )

    except Exception as e:
        return ProfileResponse(
            success=False,
            url_scraped=url,
            profile=CompanyProfile(
                about_us="Not available",
                our_culture="Not available",
                our_team="Not available",
                noteworthy_and_differentiated="Not available",
                locations="No location found",
            ),
            error=str(e),
        )


@app.post("/scrape/media", response_model=MediaResponse)
async def scrape_media(request: ScrapeRequest):
    """
    Scrape a website for media content only.

    This endpoint will:
    1. Extract media from HTML and AI analysis
    2. Download and process media files
    3. Add metadata (dimensions, size) and priority scoring
    4. Optionally include base64 data if requested

    Media items are returned sorted by priority (logos first, etc.).
    Cache headers are included for efficient mobile app usage.
    """
    try:
        url = str(request.url)
        scrape_url = find_about_page(url)

        # Extract media from HTML first
        media_items = []
        html_media = extract_media_from_html(scrape_url)

        # Try AI extraction if we have an API key
        if request.openai_api_key or DEFAULT_OPENAI_API_KEY:
            api_key = request.openai_api_key or DEFAULT_OPENAI_API_KEY
            graph_config = {
                "llm": {
                    "api_key": api_key,
                    "model": request.model,
                },
            }

            try:
                smart_scraper_graph = SmartScraperGraph(
                    prompt=default_prompt, source=scrape_url, config=graph_config
                )

                result = smart_scraper_graph.run()
                if result:
                    ai_media = extract_media_from_ai_result(result)
                    html_media.extend(ai_media)
            except Exception as e:
                print(f"AI extraction failed: {str(e)}")

        # Process all found media
        seen_urls = set()
        for media_url, media_type, context in html_media:
            if media_url not in seen_urls:
                seen_urls.add(media_url)

                url, type_, base64_data, filename, metadata, priority, ctx = (
                    download_media_to_base64(media_url, scrape_url, context)
                )

                if url:  # Only add if download successful
                    # Include base64 data only if requested
                    b64 = base64_data if request.include_base64 else None

                    media_items.append(
                        MediaItem(
                            url=url,
                            type=type_,
                            context=ctx,
                            metadata=metadata,
                            base64_data=b64,
                            filename=filename,
                            priority=priority,
                        )
                    )

        # Sort by priority (highest first)
        media_items.sort(key=lambda x: x.priority, reverse=True)

        # Add cache headers (24 hours for media list)
        headers = {"Cache-Control": "public, max-age=86400", "Vary": "Accept-Encoding"}

        return (
            MediaResponse(success=True, url_scraped=scrape_url, media=media_items),
            headers,
        )

    except Exception as e:
        return MediaResponse(success=False, url_scraped=url, media=[], error=str(e))


@app.post("/scrape/combined", response_model=CombinedResponse)
async def scrape_combined(request: ScrapeRequest):
    """
    Scrape both profile and media in a single request.

    While this endpoint is convenient, it's recommended to use
    the separate profile and media endpoints for better performance
    in mobile apps.
    """
    try:
        profile_response = await scrape_profile(request)
        media_response = await scrape_media(request)

        return CombinedResponse(
            success=profile_response.success and media_response.success,
            url_scraped=profile_response.url_scraped,
            profile=profile_response.profile,
            media=media_response.media,
            error=profile_response.error or media_response.error,
        )
    except Exception as e:
        return CombinedResponse(
            success=False,
            url_scraped=str(request.url),
            profile=CompanyProfile(
                about_us="Not available",
                our_culture="Not available",
                our_team="Not available",
                noteworthy_and_differentiated="Not available",
                locations="No location found",
            ),
            media=[],
            error=str(e),
        )


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "AI Web Scraper API is running", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "api": "AI Web Scraper",
        "version": "1.0.0",
        "features": [
            "Company profile extraction",
            "Automatic About page discovery",
            "Media extraction and base64 encoding",
            "Smart content navigation",
        ],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
