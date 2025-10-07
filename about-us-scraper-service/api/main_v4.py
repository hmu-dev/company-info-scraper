"""
AI Web Scraper API - Version 4.0
Matches remote development team schema requirements.
"""

import base64
import re
import time
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="AI Web Scraper API - Version 4.0",
    description="""
    🌐 **Web Scraping API - Remote Team Compatible Schema**
    
    This API version matches the exact schema requirements from the remote development team.
    
    ## 🎯 **Schema Compatibility:**
    - ✅ Matches required `statusCode`, `message`, `scrapingData` structure
    - ✅ Sections format with `name`, `content_summary`, `raw_excerpt`
    - ✅ Key-values as array of `{key, value}` pairs
    - ✅ Media structure with `{images: [], videos: []}`
    - ✅ Additional fields: `language`, `notes`
    
    ## 🚀 **Endpoints:**
    - `GET /scrape/text` - Text extraction matching remote team schema
    - `GET /health` - Health check
    
    ## 📝 **Example Response:**
    ```json
    {
      "statusCode": 200,
      "message": "URL scraping completed successfully",
      "scrapingData": {
        "page_title": "Company Name",
        "url": "https://example.com",
        "language": "en",
        "summary": "Company summary...",
        "sections": [...],
        "key_values": [...],
        "media": {"images": [], "videos": []},
        "notes": null
      }
    }
    ```
    """,
    version="4.0.0",
    contact={
        "name": "API Support",
        "email": "support@example.com",
        "url": "https://example.com/support",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def normalize_url(url: str) -> str:
    """Normalize URL by adding protocol if missing"""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url


def get_page_content(url: str) -> tuple[BeautifulSoup, str, int]:
    """Fetch and parse webpage content with comprehensive headers to avoid blocking"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Cache-Control": "max-age=0",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=20, allow_redirects=True)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, "html.parser")
        
        # Remove scripts and styles
        for script in soup(["script", "style"]):
            script.decompose()
            
        return soup, response.text, response.status_code
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {str(e)}")


def extract_page_language(soup: BeautifulSoup) -> Optional[str]:
    """Extract page language from HTML"""
    html_tag = soup.find("html")
    if html_tag and html_tag.get("lang"):
        return html_tag.get("lang")
    
    # Try meta tag
    meta_lang = soup.find("meta", attrs={"http-equiv": "content-language"})
    if meta_lang:
        return meta_lang.get("content")
    
    return None


def extract_sections(soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
    """Extract content sections with summaries and excerpts"""
    sections = []
    
    # Common section patterns
    section_patterns = [
        # Headings
        (soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]), "heading"),
        # Common section classes
        (soup.find_all("div", class_=re.compile(r"section|about|mission|team|contact", re.I)), "div"),
        # Articles
        (soup.find_all("article"), "article"),
        # Main content areas
        (soup.find_all(["main", "section"]), "main"),
    ]
    
    processed_content = set()
    
    for elements, element_type in section_patterns:
        for element in elements:
            # Skip if already processed
            element_text = element.get_text(strip=True)
            if not element_text or element_text in processed_content:
                continue
            
            # Get section name
            section_name = "Content"
            if element_type == "heading":
                section_name = element_text[:50] + "..." if len(element_text) > 50 else element_text
            elif element.get("class"):
                class_name = " ".join(element.get("class"))
                section_name = class_name.replace("-", " ").replace("_", " ").title()
            
            # Get content summary (first 200 chars)
            content_summary = element_text[:300] + "..." if len(element_text) > 300 else element_text
            
            # Get raw excerpt (first 100 chars)
            raw_excerpt = element_text[:150] + "..." if len(element_text) > 150 else element_text
            
            sections.append({
                "name": section_name,
                "content_summary": content_summary,
                "raw_excerpt": raw_excerpt
            })
            
            processed_content.add(element_text)
            
            # Limit to 10 sections
            if len(sections) >= 10:
                break
        
        if len(sections) >= 10:
            break
    
    return sections


def extract_key_values(soup: BeautifulSoup, text_content: str) -> List[Dict[str, str]]:
    """Extract key-value pairs from content"""
    key_values = []
    text_lower = text_content.lower()
    
    # Common patterns for key-value extraction
    patterns = [
        (r"founded\s+in?\s*:?\s*(\d{4})", "Founded"),
        (r"established\s+in?\s*:?\s*(\d{4})", "Founded"),
        (r"since\s+(\d{4})", "Founded"),
        (r"(\d+(?:,\d+)*)\s+employees?", "Employees"),
        (r"based\s+in\s+([^,\.!?]+)", "Location"),
        (r"located\s+in\s+([^,\.!?]+)", "Location"),
        (r"headquarters?\s*:?\s*([^,\.!?]+)", "Headquarters"),
        (r"industry\s*:?\s*([^,\.!?]+)", "Industry"),
        (r"specializ(?:e|ing)\s+in\s+([^,\.!?]+)", "Specialization"),
        (r"awards?\s*:?\s*([^,\.!?]+)", "Awards"),
        (r"certifications?\s*:?\s*([^,\.!?]+)", "Certifications"),
    ]
    
    for pattern, key in patterns:
        matches = re.finditer(pattern, text_lower)
        for match in matches:
            value = match.group(1).strip()
            if value and len(value) > 1:
                key_values.append({
                    "key": key,
                    "value": value.title()
                })
    
    # Remove duplicates
    seen = set()
    unique_key_values = []
    for kv in key_values:
        kv_tuple = (kv["key"], kv["value"])
        if kv_tuple not in seen:
            seen.add(kv_tuple)
            unique_key_values.append(kv)
    
    return unique_key_values[:10]  # Limit to 10 key-value pairs


def extract_media_simple(soup: BeautifulSoup, base_url: str) -> Dict[str, List[str]]:
    """Extract media URLs in simple format matching remote team schema"""
    images = []
    videos = []
    
    # Extract images
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or img.get("data-lazy-src")
        if src:
            full_url = urljoin(base_url, src)
            images.append(full_url)
    
    # Extract videos with enhanced thumbnail support
    for video in soup.find_all(["video", "iframe"]):
        src = video.get("src") or video.get("data-src")
        if src:
            full_url = urljoin(base_url, src)
            
            # Check if this is a video (not just any iframe)
            is_video = (
                video.name == "video" or 
                any(platform in full_url.lower() for platform in [
                    'youtube', 'vimeo', 'dailymotion', 'wistia', 
                    'video', '.mp4', '.webm', '.ogg'
                ])
            )
            
            if is_video:
                videos.append(full_url)
    
    return {
        "images": images[:20],  # Limit to 20 images
        "videos": videos[:10]   # Limit to 10 videos
    }


def extract_media_with_thumbnails(soup: BeautifulSoup, base_url: str) -> Dict[str, Any]:
    """Extract media with enhanced video thumbnail support"""
    try:
        from .utils.video_thumbnails import extract_video_thumbnails_from_soup
        
        # Extract basic media
        basic_media = extract_media_simple(soup, base_url)
        
        # Extract video thumbnails
        video_thumbnails = extract_video_thumbnails_from_soup(soup, base_url)
        
        # Add thumbnail info to videos
        enhanced_videos = []
        for video_url in basic_media["videos"]:
            video_info = {"url": video_url}
            
            # Find matching thumbnail
            for thumbnail in video_thumbnails:
                if thumbnail["video_url"] == video_url:
                    video_info["thumbnail_url"] = thumbnail["thumbnail_url"]
                    video_info["thumbnail_type"] = thumbnail["thumbnail_type"]
                    video_info["thumbnail_source"] = thumbnail["source"]
                    if thumbnail.get("is_placeholder"):
                        video_info["is_placeholder_thumbnail"] = True
                    break
            
            enhanced_videos.append(video_info)
        
        return {
            "images": basic_media["images"],
            "videos": enhanced_videos,
            "video_thumbnails": video_thumbnails
        }
        
    except ImportError:
        # Fallback to basic extraction if video thumbnails module not available
        return extract_media_simple(soup, base_url)


def generate_summary(text_content: str, page_title: str) -> str:
    """Generate a summary from the page content"""
    # Clean and extract first few sentences
    sentences = re.split(r'[.!?]+', text_content)
    clean_sentences = [s.strip() for s in sentences if s.strip() and len(s.strip()) > 20]
    
    if clean_sentences:
        summary = ". ".join(clean_sentences[:3])
        if not summary.endswith("."):
            summary += "."
        return summary
    
    # Fallback to title-based summary
    return f"{page_title} provides information about their services and offerings."


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "4.0.0",
        "approach": "remote_team_compatible"
    }


@app.get("/scrape/text")
async def scrape_text_v4(
    url: str = Query(..., description="The URL to scrape"),
    max_sections: int = Query(10, description="Maximum number of sections to extract", le=20),
    max_key_values: int = Query(10, description="Maximum number of key-value pairs to extract", le=20)
):
    """
    🌐 **TEXT EXTRACTION - Remote Team Compatible Schema**
    
    Extracts text content from a website and returns it in the exact schema format
    required by the remote development team.
    
    ### **Response Schema:**
    - `statusCode`: HTTP status code
    - `message`: Success/error message  
    - `scrapingData`: Main content with sections, key-values, and media
    
    ### **Example:**
    ```bash
    GET /scrape/text?url=ambiancesf.com/pages/about
    ```
    """
    start_time = time.time()
    
    try:
        # Normalize and fetch URL
        normalized_url = normalize_url(url)
        soup, html_content, status_code = get_page_content(normalized_url)
        
        # Extract page title
        title_tag = soup.find("title")
        page_title = title_tag.get_text().strip() if title_tag else "Untitled Page"
        
        # Extract language
        language = extract_page_language(soup)
        
        # Get main text content
        text_content = soup.get_text()
        # Clean up text
        lines = (line.strip() for line in text_content.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text_content = " ".join(chunk for chunk in chunks if chunk)
        
        # Generate summary
        summary = generate_summary(text_content, page_title)
        
        # Extract sections
        sections = extract_sections(soup, normalized_url)[:max_sections]
        
        # Extract key-value pairs
        key_values = extract_key_values(soup, text_content)[:max_key_values]
        
        # Extract media
        media = extract_media_with_thumbnails(soup, normalized_url)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Build response matching remote team schema
        response = {
            "statusCode": 200,
            "message": "URL scraping completed successfully",
            "scrapingData": {
                "page_title": page_title,
                "url": normalized_url,
                "language": language,
                "summary": summary,
                "sections": sections,
                "key_values": key_values,
                "media": media,
                "notes": f"Processed in {processing_time:.2f} seconds"
            }
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        return {
            "statusCode": 500,
            "message": f"Scraping failed: {str(e)}",
            "scrapingData": None
        }


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "AI Web Scraper API - Version 4.0",
        "description": "Remote team compatible schema",
        "version": "4.0.0",
        "docs": "/docs",
        "health": "/health"
    }


