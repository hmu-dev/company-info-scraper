from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup
import json
import re
import time
from urllib.parse import urljoin, urlparse
from typing import Dict, Any, List, Optional, Tuple

app = FastAPI(
    title="AI Web Scraper API - Hybrid Approach",
    description="Smart web scraping API with programmatic + AI hybrid approach",
    version="2.0.0",
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
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    return url

def get_page_content(url: str) -> Tuple[BeautifulSoup, str, int]:
    """Fetch and parse webpage content"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'html.parser')
    return soup, response.text, response.status_code

def extract_media_assets(soup: BeautifulSoup, base_url: str) -> Dict[str, List[Dict]]:
    """Extract all media assets from the webpage"""
    media_assets = {
        "images": [],
        "videos": [],
        "audio": [],
        "documents": [],
        "icons": []
    }
    
    # Extract images
    for img in soup.find_all('img'):
        src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
        if src:
            full_url = urljoin(base_url, src)
            media_assets["images"].append({
                "url": full_url,
                "alt": img.get('alt', ''),
                "title": img.get('title', ''),
                "width": img.get('width', ''),
                "height": img.get('height', ''),
                "class": img.get('class', []),
                "priority": "high" if any(keyword in (img.get('alt', '') + ' ' + ' '.join(img.get('class', []))).lower() 
                           for keyword in ['logo', 'brand', 'company']) else "medium"
            })
    
    # Extract videos
    for video in soup.find_all(['video', 'iframe']):
        src = video.get('src') or video.get('data-src')
        if src:
            full_url = urljoin(base_url, src)
            media_assets["videos"].append({
                "url": full_url,
                "type": "video" if video.name == "video" else "iframe",
                "poster": video.get('poster', ''),
                "title": video.get('title', ''),
                "class": video.get('class', [])
            })
    
    # Extract audio
    for audio in soup.find_all('audio'):
        src = audio.get('src')
        if src:
            full_url = urljoin(base_url, src)
            media_assets["audio"].append({
                "url": full_url,
                "title": audio.get('title', ''),
                "class": audio.get('class', [])
            })
    
    # Extract documents (PDFs, DOCs, etc.)
    for link in soup.find_all('a', href=True):
        href = link.get('href')
        if href:
            full_url = urljoin(base_url, href)
            parsed_url = urlparse(full_url)
            file_ext = parsed_url.path.lower().split('.')[-1] if '.' in parsed_url.path else ''
            
            if file_ext in ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx']:
                media_assets["documents"].append({
                    "url": full_url,
                    "filename": parsed_url.path.split('/')[-1],
                    "extension": file_ext,
                    "text": link.get_text().strip(),
                    "title": link.get('title', '')
                })
    
    # Extract favicons and icons
    for link in soup.find_all('link', rel=True):
        rel = link.get('rel')
        href = link.get('href')
        if href and any(icon_type in rel for icon_type in ['icon', 'shortcut', 'apple-touch-icon']):
            full_url = urljoin(base_url, href)
            media_assets["icons"].append({
                "url": full_url,
                "rel": rel,
                "sizes": link.get('sizes', ''),
                "type": link.get('type', '')
            })
    
    return media_assets

def find_about_pages(soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
    """Find potential About Us pages from navigation and links"""
    about_pages = []
    
    # Common about page patterns
    about_patterns = [
        r'/about',
        r'/about-us',
        r'/about-our-company',
        r'/company',
        r'/team',
        r'/our-story',
        r'/who-we-are',
        r'/mission',
        r'/values'
    ]
    
    # Look for navigation links
    nav_links = soup.find_all(['nav', 'header', 'footer'])
    for nav in nav_links:
        for link in nav.find_all('a', href=True):
            href = link.get('href', '').lower()
            text = link.get_text().strip().lower()
            
            # Check if link text or URL matches about patterns
            for pattern in about_patterns:
                if re.search(pattern, href) or any(keyword in text for keyword in ['about', 'company', 'team', 'story']):
                    full_url = urljoin(base_url, link.get('href'))
                    about_pages.append({
                        "url": full_url,
                        "text": link.get_text().strip(),
                        "confidence": "high" if any(keyword in text for keyword in ['about', 'company']) else "medium"
                    })
                    break
    
    # Remove duplicates and sort by confidence
    unique_pages = []
    seen_urls = set()
    for page in about_pages:
        if page["url"] not in seen_urls:
            unique_pages.append(page)
            seen_urls.add(page["url"])
    
    return sorted(unique_pages, key=lambda x: 0 if x["confidence"] == "high" else 1)

def extract_company_info_programmatic(text_content: str) -> Dict[str, Any]:
    """Extract company information using programmatic pattern matching"""
    company_info = {
        "founded": None,
        "employees": None,
        "location": None,
        "mission": None,
        "industry": None,
        "ceo": None,
        "confidence": "programmatic"
    }
    
    text_lower = text_content.lower()
    
    # Enhanced pattern matching
    patterns = {
        "founded": [
            r'founded\s+in?\s+(\d{4})',
            r'established\s+in?\s+(\d{4})',
            r'since\s+(\d{4})',
            r'(\d{4})\s+to\s+present',
            r'started\s+in?\s+(\d{4})'
        ],
        "employees": [
            r'(\d+(?:,\d+)*)\s+employees?',
            r'team\s+of\s+(\d+(?:,\d+)*)',
            r'over\s+(\d+(?:,\d+)*)\s+people',
            r'(\d+(?:,\d+)*)\s+staff',
            r'(\d+(?:,\d+)*)\s+team\s+members?'
        ],
        "location": [
            r'based\s+in\s+([^,\.]+)',
            r'headquartered\s+in\s+([^,\.]+)',
            r'located\s+in\s+([^,\.]+)',
            r'from\s+([^,\.]+)',
            r'office\s+in\s+([^,\.]+)'
        ],
        "ceo": [
            r'ceo[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)',
            r'chief\s+executive\s+officer[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)',
            r'president[:\s]+([A-Z][a-z]+ [A-Z][a-z]+)'
        ]
    }
    
    for field, pattern_list in patterns.items():
        for pattern in pattern_list:
            match = re.search(pattern, text_lower)
            if match:
                company_info[field] = match.group(1).strip()
                break
    
    # Calculate confidence based on how much info we found
    found_fields = sum(1 for v in company_info.values() if v and v != "programmatic")
    if found_fields >= 3:
        company_info["confidence"] = "high"
    elif found_fields >= 1:
        company_info["confidence"] = "medium"
    else:
        company_info["confidence"] = "low"
    
    return company_info

def should_use_ai(company_info: Dict[str, Any], text_content: str) -> bool:
    """Determine if we should use AI based on programmatic results"""
    # Use AI if confidence is low or we found very little information
    if company_info["confidence"] == "low":
        return True
    
    # Use AI if text content is very short (might be missing context)
    if len(text_content) < 500:
        return True
    
    # Use AI if we didn't find key information
    key_fields = ["founded", "employees", "location"]
    found_key_fields = sum(1 for field in key_fields if company_info.get(field))
    
    if found_key_fields < 2:
        return True
    
    return False

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "2.0.0", "approach": "hybrid"}

@app.get("/scrape/intelligent")
async def scrape_intelligent(
    url: str,
    force_ai: bool = Query(False, description="Force AI analysis even if programmatic results are good"),
    max_about_pages: int = Query(3, description="Maximum number of about pages to analyze"),
    include_media: bool = Query(True, description="Include media asset extraction")
):
    """
    🧠 HYBRID INTELLIGENT SCRAPING ENDPOINT
    
    This endpoint combines the best of both worlds:
    1. ⚡ FAST: Starts with programmatic extraction
    2. 🧠 SMART: Falls back to AI when needed
    3. 🔍 AUTO-DISCOVERY: Finds About Us pages automatically
    4. 📸 COMPLETE: Extracts media assets and company info
    
    Args:
        url: The URL to scrape (can be domain or specific page)
        force_ai: Force AI analysis even if programmatic results are good
        max_about_pages: Maximum number of about pages to analyze
        include_media: Include media asset extraction
    
    Returns:
        Complete company analysis with media assets
    """
    start_time = time.time()
    
    try:
        url = normalize_url(url)
        
        # Step 1: Get main page content
        soup, html_content, status_code = get_page_content(url)
        
        # Step 2: Extract basic information
        title = soup.find('title')
        title_text = title.get_text().strip() if title else "No title found"
        
        meta_description = soup.find('meta', attrs={'name': 'description'})
        description = meta_description.get('content', '') if meta_description else "No description found"
        
        # Clean up content
        for script in soup(["script", "style"]):
            script.decompose()
        
        text_content = soup.get_text()
        lines = (line.strip() for line in text_content.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text_content = ' '.join(chunk for chunk in chunks if chunk)
        
        # Step 3: Find About Us pages
        about_pages = find_about_pages(soup, url)
        
        # Step 4: Analyze About pages if found
        all_about_content = text_content  # Start with main page content
        best_about_url = url
        about_page_analysis = []
        
        for about_page in about_pages[:max_about_pages]:
            try:
                about_soup, about_html, about_status = get_page_content(about_page["url"])
                about_text = about_soup.get_text()
                
                # Clean up about page text
                about_lines = (line.strip() for line in about_text.splitlines())
                about_chunks = (phrase.strip() for line in about_lines for phrase in line.split("  "))
                about_text_clean = ' '.join(chunk for chunk in about_chunks if chunk)
                
                # If this about page has more content, use it
                if len(about_text_clean) > len(all_about_content):
                    all_about_content = about_text_clean
                    best_about_url = about_page["url"]
                
                about_page_analysis.append({
                    "url": about_page["url"],
                    "title": about_soup.find('title').get_text().strip() if about_soup.find('title') else "",
                    "content_length": len(about_text_clean),
                    "confidence": about_page["confidence"]
                })
                
            except Exception as e:
                # Skip problematic about pages
                continue
        
        # Step 5: Extract company info programmatically
        company_info = extract_company_info_programmatic(all_about_content)
        
        # Step 6: Extract media assets if requested
        media_assets = {}
        media_summary = {}
        if include_media:
            media_assets = extract_media_assets(soup, url)
            media_summary = {
                "total_assets": sum(len(assets) for assets in media_assets.values()),
                "images_count": len(media_assets["images"]),
                "videos_count": len(media_assets["videos"]),
                "documents_count": len(media_assets["documents"]),
                "icons_count": len(media_assets["icons"])
            }
            
            # Sort images by priority (logos first)
            media_assets["images"].sort(key=lambda x: 0 if x["priority"] == "high" else 1)
        
        # Step 7: Determine if we need AI
        use_ai = force_ai or should_use_ai(company_info, all_about_content)
        
        # Step 8: AI Enhancement (placeholder for now)
        ai_enhancement = {}
        if use_ai:
            ai_enhancement = {
                "used": True,
                "reason": "Low confidence programmatic results" if company_info["confidence"] == "low" else "Forced by parameter",
                "note": "AI enhancement would be implemented here with Bedrock/Claude"
            }
            # In a real implementation, you would call your AI service here
            # ai_results = await call_ai_service(all_about_content)
        else:
            ai_enhancement = {
                "used": False,
                "reason": "Programmatic results were sufficient",
                "note": "Fast path taken - no AI needed"
            }
        
        # Step 9: Calculate performance metrics
        processing_time = time.time() - start_time
        
        # Step 10: Return comprehensive results
        return {
            "success": True,
            "url": url,
            "best_about_url": best_about_url,
            "title": title_text,
            "description": description,
            "content": all_about_content[:3000] + "..." if len(all_about_content) > 3000 else all_about_content,
            "company_info": company_info,
            "about_pages_found": len(about_pages),
            "about_page_analysis": about_page_analysis,
            "media_assets": media_assets if include_media else None,
            "media_summary": media_summary if include_media else None,
            "ai_enhancement": ai_enhancement,
            "processing_time_seconds": round(processing_time, 2),
            "approach_used": "ai_enhanced" if use_ai else "programmatic",
            "status_code": status_code,
            "content_type": "application/json"
        }
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

@app.get("/scrape/fast")
async def scrape_fast(url: str, include_media: bool = Query(True, description="Include media asset extraction")):
    """
    ⚡ FAST SCRAPING ENDPOINT
    
    Pure programmatic approach for maximum speed:
    - No AI processing
    - Basic pattern matching
    - Media extraction
    - About page discovery
    
    Args:
        url: The URL to scrape
        include_media: Include media asset extraction
    
    Returns:
        Fast scraped results
    """
    start_time = time.time()
    
    try:
        url = normalize_url(url)
        soup, html_content, status_code = get_page_content(url)
        
        # Basic extraction
        title = soup.find('title')
        title_text = title.get_text().strip() if title else "No title found"
        
        meta_description = soup.find('meta', attrs={'name': 'description'})
        description = meta_description.get('content', '') if meta_description else "No description found"
        
        for script in soup(["script", "style"]):
            script.decompose()
        
        text_content = soup.get_text()
        lines = (line.strip() for line in text_content.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text_content = ' '.join(chunk for chunk in chunks if chunk)
        
        # Extract company info
        company_info = extract_company_info_programmatic(text_content)
        
        # Extract media if requested
        media_assets = {}
        media_summary = {}
        if include_media:
            media_assets = extract_media_assets(soup, url)
            media_summary = {
                "total_assets": sum(len(assets) for assets in media_assets.values()),
                "images_count": len(media_assets["images"]),
                "videos_count": len(media_assets["videos"]),
                "documents_count": len(media_assets["documents"]),
                "icons_count": len(media_assets["icons"])
            }
        
        processing_time = time.time() - start_time
        
        return {
            "success": True,
            "url": url,
            "title": title_text,
            "description": description,
            "content": text_content[:2000] + "..." if len(text_content) > 2000 else text_content,
            "company_info": company_info,
            "media_assets": media_assets if include_media else None,
            "media_summary": media_summary if include_media else None,
            "processing_time_seconds": round(processing_time, 2),
            "approach_used": "fast_programmatic",
            "status_code": status_code
        }
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

# Keep existing endpoints for backward compatibility
@app.get("/scrape")
async def scrape_url(url: str):
    """Legacy basic scraping endpoint"""
    return await scrape_fast(url, include_media=False)

@app.get("/scrape/about")
async def scrape_about_page(url: str):
    """Legacy about page scraping endpoint"""
    return await scrape_fast(url, include_media=False)
