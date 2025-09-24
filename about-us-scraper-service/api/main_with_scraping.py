from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup
import json
from typing import Dict, Any

app = FastAPI(
    title="AI Web Scraper API",
    description="Web scraping API with basic functionality",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/scrape")
async def scrape_url(url: str):
    """
    Scrape a URL and return basic information
    
    Args:
        url: The URL to scrape
        
    Returns:
        Basic scraped data including title, meta description, and text content
    """
    try:
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        # Fetch the webpage
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract basic information
        title = soup.find('title')
        title_text = title.get_text().strip() if title else "No title found"
        
        meta_description = soup.find('meta', attrs={'name': 'description'})
        description = meta_description.get('content', '') if meta_description else "No description found"
        
        # Get main text content (remove scripts and styles)
        for script in soup(["script", "style"]):
            script.decompose()
        
        text_content = soup.get_text()
        # Clean up text
        lines = (line.strip() for line in text_content.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text_content = ' '.join(chunk for chunk in chunks if chunk)
        
        # Limit text content to first 1000 characters
        text_content = text_content[:1000] + "..." if len(text_content) > 1000 else text_content
        
        # Extract links
        links = []
        for link in soup.find_all('a', href=True):
            href = link['href']
            text = link.get_text().strip()
            if text and href:
                links.append({"text": text, "url": href})
        
        # Limit links to first 10
        links = links[:10]
        
        return {
            "success": True,
            "url": url,
            "title": title_text,
            "description": description,
            "text_content": text_content,
            "links": links,
            "status_code": response.status_code,
            "content_type": response.headers.get('content-type', 'unknown')
        }
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

@app.get("/scrape/about")
async def scrape_about_page(url: str):
    """
    Scrape an 'About Us' page and extract company information
    
    Args:
        url: The URL to scrape (should be an About Us page)
        
    Returns:
        Extracted company information
    """
    try:
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove scripts and styles
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Extract title
        title = soup.find('title')
        title_text = title.get_text().strip() if title else "No title found"
        
        # Extract main content
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=['content', 'main-content', 'about-content'])
        
        if main_content:
            text_content = main_content.get_text()
        else:
            text_content = soup.get_text()
        
        # Clean up text
        lines = (line.strip() for line in text_content.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text_content = ' '.join(chunk for chunk in chunks if chunk)
        
        # Look for company information patterns
        company_info = {
            "founded": None,
            "employees": None,
            "location": None,
            "mission": None
        }
        
        # Simple pattern matching for company info
        text_lower = text_content.lower()
        
        # Look for founding year
        import re
        founded_match = re.search(r'founded\s+in?\s+(\d{4})', text_lower)
        if founded_match:
            company_info["founded"] = founded_match.group(1)
        
        # Look for employee count
        employee_match = re.search(r'(\d+(?:,\d+)*)\s+employees?', text_lower)
        if employee_match:
            company_info["employees"] = employee_match.group(1)
        
        # Look for location
        location_match = re.search(r'based\s+in\s+([^,\.]+)', text_lower)
        if location_match:
            company_info["location"] = location_match.group(1).strip()
        
        return {
            "success": True,
            "url": url,
            "title": title_text,
            "content": text_content[:2000] + "..." if len(text_content) > 2000 else text_content,
            "company_info": company_info,
            "status_code": response.status_code
        }
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")
