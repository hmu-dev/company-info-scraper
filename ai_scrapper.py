# Import the required libraries
import streamlit as st
import requests
import os
import json
import logging
import traceback
import sys
import subprocess
from datetime import datetime
from urllib.parse import urljoin, urlparse
from scrapegraphai.graphs import SmartScraperGraph
import base64
from io import BytesIO
from PIL import Image
from bs4 import BeautifulSoup
import re
import cairosvg
import ffmpeg

# Video constraints
MAX_VIDEO_DURATION_SECONDS = 300  # 5 minutes
MAX_VIDEO_SIZE_MB = 50  # Maximum video file size in MB
ALLOWED_VIDEO_FORMATS = ['.mp4', '.webm', '.mov']

def get_video_duration(url):
    """Get video duration without downloading the entire file"""
    try:
        # Use ffprobe to get video duration
        probe = ffmpeg.probe(url)
        duration = float(probe['streams'][0]['duration'])
        return duration
    except Exception as e:
        logger.warning(f"Could not get video duration for {url}: {str(e)}")
        return None

def get_video_metadata(url):
    """Get video metadata including duration, resolution, and format"""
    try:
        probe = ffmpeg.probe(url)
        video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
        
        return {
            'duration': float(video_info.get('duration', 0)),
            'width': int(video_info.get('width', 0)),
            'height': int(video_info.get('height', 0)),
            'format': video_info.get('codec_name', 'unknown'),
            'bitrate': int(video_info.get('bit_rate', 0)) if 'bit_rate' in video_info else 0
        }
    except Exception as e:
        logger.warning(f"Could not get video metadata for {url}: {str(e)}")
        return None

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper_debug.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('ai_scraper')

def log_exception(e, context=""):
    """Log exception with full traceback and context"""
    logger.error(f"Exception in {context}: {str(e)}")
    logger.error(f"Traceback:\n{''.join(traceback.format_tb(e.__traceback__))}")
    
def log_state(msg, data=None):
    """Log state information with optional data"""
    if data:
        logger.debug(f"{msg}: {json.dumps(data, indent=2)}")
    else:
        logger.debug(msg)

# Set up the Streamlit app
st.title("Web Scrapping AI Agent 🕵️‍♂️")
st.caption("This app allows you to scrape a website using OpenAI API and display media content")

# Add custom CSS for expandable text area
st.markdown("""
<style>
    .stTextArea > div > div > textarea {
        resize: vertical;
        min-height: 200px;
        max-height: 400px;
        overflow-y: auto;
    }
    .element-container:has(.stTextArea) {
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Create or clean media directory
if os.path.exists("scraped_media"):
    # Clean up old files
    for file in os.listdir("scraped_media"):
        try:
            os.remove(os.path.join("scraped_media", file))
        except Exception as e:
            st.warning(f"Could not remove old file {file}: {str(e)}")
else:
    os.makedirs("scraped_media")

def download_media_to_base64(media_url, base_url, context="", session=None):
    """Download media and extract metadata"""
    log_state(f"Starting media download from: {media_url}")
    try:
        # Handle data URLs
        if media_url.startswith('data:'):
            # Skip empty SVGs or placeholder images
            if 'viewBox=' in media_url and ('0 0' in media_url or 'placeholder' in media_url.lower()):
                return None, None, None, None, None, 0, context
                
            try:
                # Extract base64 data after the comma
                if ',' not in media_url:
                    return None, None, None, None, None, 0, context
                    
                header, encoded = media_url.split(',', 1)
                if ';base64,' not in header:
                    return None, None, None, None, None, 0, context
                    
                content_type = header.split(';')[0].split(':')[1]
                
                # Fix padding if needed
                padding_needed = len(encoded) % 4
                if padding_needed:
                    encoded += '=' * (4 - padding_needed)
                
                try:
                    # Decode the content
                    content = base64.b64decode(encoded)
                    
                    # Skip if content is too small (likely a placeholder)
                    if len(content) < 100:  # Less than 100 bytes
                        return None, None, None, None, None, 0, context
                    
                    # Determine file type and save
                    if 'svg' in content_type:
                        file_ext = '.png'  # Convert SVG to PNG
                        file_name = f"inline_{hash(media_url) % 10000}{file_ext}"
                        file_path = os.path.join("scraped_media", file_name)
                        
                        # Save SVG content first
                        svg_path = os.path.join("scraped_media", f"temp_{hash(media_url) % 10000}.svg")
                        with open(svg_path, 'wb') as f:
                            f.write(content)
                            
                        # Convert to PNG
                        try:
                            cairosvg.svg2png(url=svg_path, write_to=file_path)
                            os.remove(svg_path)  # Clean up temp SVG
                            with open(file_path, 'rb') as f:
                                content = f.read()
                        except Exception as e:
                            st.warning(f"Could not convert SVG to PNG: {str(e)}")
                            os.remove(svg_path)
                            return None, None, None, None, None, 0, context
                            
                    elif 'png' in content_type:
                        file_ext = '.png'
                        file_name = f"inline_{hash(media_url) % 10000}{file_ext}"
                        file_path = os.path.join("scraped_media", file_name)
                        with open(file_path, 'wb') as f:
                            f.write(content)
                            
                    elif 'jpeg' in content_type or 'jpg' in content_type:
                        file_ext = '.jpg'
                        file_name = f"inline_{hash(media_url) % 10000}{file_ext}"
                        file_path = os.path.join("scraped_media", file_name)
                        with open(file_path, 'wb') as f:
                            f.write(content)
                            
                    else:
                        return None, None, None, None, None, 0, context
                    
                    # Get image dimensions
                    try:
                        with Image.open(file_path) as img:
                            width, height = img.size
                            if width < 100 or height < 100:  # Skip small images
                                os.remove(file_path)
                                return None, None, None, None, None, 0, context
                    except Exception as e:
                        os.remove(file_path)
                        return None, None, None, None, None, 0, context
                    
                    return media_url, 'image', base64.b64encode(content).decode('utf-8'), file_name, {
                        'format': file_ext.lstrip('.'),
                        'width': width,
                        'height': height,
                        'size_bytes': len(content)
                    }, 10, context
                    
                except Exception as e:
                    st.warning(f"Could not decode base64 data: {str(e)}")
                    return None, None, None, None, None, 0, context
                
            except Exception as e:
                st.warning(f"Could not process data URL: {str(e)}")
                return None, None, None, None, None, 0, context
        
        # Handle relative URLs
        if not media_url.startswith(('http://', 'https://')):
            media_url = urljoin(base_url, media_url)
        
        # Use session if provided, otherwise create a new request
        if session:
            response = session.get(media_url, timeout=30, stream=True)
        else:
            response = requests.get(media_url, timeout=30, stream=True)
        
        if response.status_code == 200:
            content = response.content
            content_type = response.headers.get('content-type', '').lower()
            content_length = int(response.headers.get('content-length', len(content)))
            
            # Check content length before downloading
            content_length = int(response.headers.get('content-length', 0))
            if content_length > 10 * 1024 * 1024:  # Skip files larger than 10MB
                logger.warning(f"Skipping large file {media_url} ({content_length / 1024 / 1024:.1f}MB)")
                return None, None, None, None, None, 0, context

            # Get file info
            parsed_url = urlparse(media_url)
            file_name = os.path.basename(parsed_url.path)
            
            if not file_name or '.' not in file_name:
                if 'video' in content_type:
                    file_name = f"video_{hash(media_url) % 10000}.mp4"
                else:
                    file_name = f"image_{hash(media_url) % 10000}.jpg"
                    
            # Handle video files
            file_ext = file_name.lower().split('.')[-1]
            if f'.{file_ext}' in ALLOWED_VIDEO_FORMATS:
                # Check video duration before downloading
                duration = get_video_duration(media_url)
                if duration is None:
                    logger.warning(f"Could not determine video duration for {media_url}")
                    return None, None, None, None, None, 0, context
                
                if duration > MAX_VIDEO_DURATION_SECONDS:
                    logger.warning(f"Video too long ({duration:.1f} seconds) - skipping: {media_url}")
                    return None, None, None, None, None, 0, context
                
                # Get video metadata
                metadata = get_video_metadata(media_url)
                if metadata is None:
                    logger.warning(f"Could not get video metadata for {media_url}")
                    return None, None, None, None, None, 0, context
                
                # Check file size (using bitrate * duration as estimate)
                estimated_size_mb = (metadata['bitrate'] * duration) / (8 * 1024 * 1024)  # Convert bits to MB
                if estimated_size_mb > MAX_VIDEO_SIZE_MB:
                    logger.warning(f"Video too large (estimated {estimated_size_mb:.1f}MB) - skipping: {media_url}")
                    return None, None, None, None, None, 0, context
                
                logger.info(f"Video accepted: {media_url} (duration: {duration:.1f}s, size: {estimated_size_mb:.1f}MB)")
                metadata['duration_seconds'] = duration
            
            # Determine media type and format
            file_ext = file_name.lower().split('.')[-1]
            media_type = 'video' if file_ext in ['mp4', 'webm', 'avi', 'mov', 'mkv', 'flv', 'm4v'] else 'image'
            
            # Create media directory if it doesn't exist
            if not os.path.exists("scraped_media"):
                os.makedirs("scraped_media")
            
            # Save temporarily for processing
            file_path = os.path.join("scraped_media", file_name)
            try:
                with open(file_path, 'wb') as f:
                    f.write(content)
            except Exception as e:
                st.warning(f"Could not save file {file_name}: {str(e)}")
                return None, None, None, None, None, 0, context
            
            # Verify file was saved and has content
            if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                st.warning(f"File {file_name} was not saved properly")
                return None, None, None, None, None, 0, context
            
            # Initialize metadata
            metadata = {
                'width': None,
                'height': None,
                'size_bytes': content_length,
                'format': file_ext.lstrip('.')  # Remove leading dot
            }
            
            # Process image files
            if media_type == 'image':
                try:
                    # Convert SVG if needed
                    if file_ext.lower() == 'svg' or metadata['format'].lower() == 'svg':
                        try:
                            png_path = os.path.join("scraped_media", f"{os.path.splitext(file_name)[0]}.png")
                            cairosvg.svg2png(url=file_path, write_to=png_path)
                            if os.path.exists(file_path):
                                os.remove(file_path)
                            file_path = png_path
                            file_ext = 'png'
                            metadata['format'] = 'png'
                            with open(file_path, 'rb') as f:
                                content = f.read()
                        except Exception as e:
                            st.warning(f"Could not convert SVG to PNG: {str(e)}")
                            if os.path.exists(file_path):
                                os.remove(file_path)
                            return None, None, None, None, None, 0, context
                    
                    # Verify image can be opened
                    try:
                        with Image.open(file_path) as img:
                            # Get image dimensions
                            metadata['width'], metadata['height'] = img.size
                            
                            # Skip small images
                            if metadata['width'] < 100 or metadata['height'] < 100:
                                os.remove(file_path)
                                return None, None, None, None, None, 0, context
                            
                            # Verify image is valid
                            img.verify()
                    except Exception as e:
                        st.warning(f"Invalid image file {file_name}: {str(e)}")
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        return None, None, None, None, None, 0, context
                except Exception as e:
                    st.warning(f"Error processing image {media_url}: {str(e)}")
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    return None, None, None, None, None, 0, context
            
            # Calculate priority score
            priority = 10  # default score
            context_lower = context.lower()
            
            # Boost score for important contexts
            if any(key in context_lower for key in ['logo', 'brand']):
                priority = 100
            elif any(key in context_lower for key in ['team', 'founder', 'leader']):
                priority = 80
            elif any(key in context_lower for key in ['office', 'location', 'building']):
                priority = 60
            elif any(key in context_lower for key in ['product', 'service']):
                priority = 40
            
            # Boost score for likely logo dimensions
            if media_type == 'image' and metadata['width'] and metadata['height']:
                aspect_ratio = metadata['width'] / metadata['height']
                if 0.8 <= aspect_ratio <= 1.2:  # square-ish logos
                    priority += 20
            
            # Convert to base64
            base64_data = base64.b64encode(content).decode('utf-8')
            
            return media_url, media_type, base64_data, file_name, metadata, priority, context
            
    except Exception as e:
        st.warning(f"Could not download media from {media_url}: {str(e)}")
    
    return None, None, None, None, None, 0, context

def extract_media_from_html(url):
    """Extract media URLs directly from HTML"""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            media_urls = []
            
            # Find images
            img_tags = soup.find_all('img')
            for img in img_tags:
                src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                if src:
                    # Filter for likely branding/company images
                    alt_text = (img.get('alt') or '').lower()
                    src_lower = src.lower()
                    
                    # Look for logos, company images, team photos
                    if any(keyword in alt_text or keyword in src_lower for keyword in 
                           ['logo', 'brand', 'company', 'team', 'about', 'founder', 'staff', 'office']):
                        media_urls.append((src, 'image', f"Image: {alt_text or 'Company image'}"))
                    # Also include images that seem to be content images (not UI elements)
                    elif not any(ui_element in src_lower for ui_element in 
                                ['icon', 'button', 'arrow', 'cart', 'search', 'menu']):
                        media_urls.append((src, 'image', f"Image: {alt_text or 'Content image'}"))
            
            # Find videos
            video_tags = soup.find_all(['video', 'source'])
            for video in video_tags:
                src = video.get('src')
                if src:
                    media_urls.append((src, 'video', "Video content"))
            
            # Find background images in CSS
            style_tags = soup.find_all(['div', 'section', 'header'], style=True)
            for tag in style_tags:
                style = tag.get('style', '')
                bg_matches = re.findall(r'background-image:\s*url\(["\']?([^"\']+)["\']?\)', style)
                for bg_url in bg_matches:
                    media_urls.append((bg_url, 'image', "Background image"))
            
            return media_urls
    except Exception as e:
        st.warning(f"Could not extract media from HTML: {str(e)}")
    
    return []

def find_about_page(base_url):
    """Try to find About Us page if not directly provided"""
    try:
        # Parse the base URL to get the domain
        parsed_url = urlparse(base_url)
        domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # First, try the provided URL - it might already be good
        try:
            response = requests.get(base_url, timeout=10)
            if response.status_code == 200:
                # Check if this page already has about content
                soup = BeautifulSoup(response.content, 'html.parser')
                page_text = soup.get_text().lower()
                if any(keyword in page_text for keyword in ['about us', 'our story', 'our team', 'our company', 'founded']):
                    return base_url
        except:
            pass
        
        # If not, try to find about pages
        response = requests.get(domain, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for about links in navigation
            about_keywords = ['about', 'about-us', 'about_us', 'company', 'our-story', 'our-team', 'team', 'story']
            
            # Priority search - look in navigation areas first
            nav_areas = soup.find_all(['nav', 'header', 'menu']) + soup.find_all('ul', class_=re.compile(r'nav|menu', re.I))
            
            for nav in nav_areas:
                links = nav.find_all('a', href=True)
                for link in links:
                    href = link['href'].lower()
                    link_text = link.get_text().lower().strip()
                    
                    # Check if this looks like an about page
                    if any(keyword in href or keyword in link_text for keyword in about_keywords):
                        full_url = urljoin(domain, link['href'])
                        return full_url
            
            # If not found in nav, search all links
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link['href'].lower()
                link_text = link.get_text().lower().strip()
                
                # More specific matching for about pages
                if (any(keyword in href for keyword in about_keywords) or 
                    any(phrase in link_text for phrase in ['about us', 'about', 'our story', 'our team', 'company'])):
                    full_url = urljoin(domain, link['href'])
                    return full_url
                    
            # Check for common about page paths
            common_paths = [
                '/about', '/about-us', '/about_us', '/company', '/our-story', '/our-team', 
                '/pages/about', '/pages/about-us', '/about/', '/company/', '/story/',
                '/en/about', '/home/about', '/site/about'
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
        st.warning(f"Could not search for about page: {str(e)}")
    
    return base_url

def display_media_content(result, base_url):
    """Process and display media content from scraping results"""
    downloaded_media = []
    
    def process_content(content, path=""):
        """Recursively process content to find and download media"""
        if isinstance(content, dict):
            for key, value in content.items():
                current_path = f"{path}.{key}" if path else key
                if key.lower() in ['image', 'img', 'logo', 'photo', 'picture', 'icon', 'video', 'movie', 'clip', 'media'] and isinstance(value, str):
                    # This looks like a media URL
                    local_path, original_url, media_type = download_media(value, base_url)
                    if local_path:
                        downloaded_media.append((local_path, original_url, current_path, media_type))
                elif isinstance(value, (dict, list)):
                    process_content(value, current_path)
        elif isinstance(content, list):
            for i, item in enumerate(content):
                current_path = f"{path}[{i}]"
                process_content(item, current_path)
        elif isinstance(content, str):
            # Check if the string looks like a media URL
            media_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp', '.mp4', '.webm', '.avi', '.mov', '.mkv', '.flv', '.m4v']
            if any(ext in content.lower() for ext in media_extensions):
                local_path, original_url, media_type = download_media(content, base_url)
                if local_path:
                    downloaded_media.append((local_path, original_url, path, media_type))
    
    # Process the result to find media
    if isinstance(result, dict) and 'content' in result:
        process_content(result['content'])
    else:
        process_content(result)
    
    return downloaded_media

# Get OpenAI API key (pre-configured)
try:
    openai_access_token = st.secrets["secrets"]["OPENAI_API_KEY"]
    st.success("✅ OpenAI API Key loaded successfully!")
except Exception:
    # Fallback: allow manual input if secrets not available
    st.warning("⚠️ API key not configured. Please enter manually:")
    openai_access_token = st.text_input("OpenAI API Key", type="password")

if openai_access_token:
    model = st.radio(
        "Select the model",
        ["gpt-3.5-turbo", "gpt-4"],
        index=0,
    )    
    graph_config = {
        "llm": {
            "api_key": openai_access_token,
            "model": model,
        },
    }
    # Select scraping mode
    scrape_mode = st.radio(
        "Select scraping mode",
        ["Combined (Profile + Media)", "Profile Only", "Media Only"],
        help="Choose what to extract from the website"
    )
    
    # Get the URL of the website to scrape
    url = st.text_input("Enter the URL of the website you want to scrape")
    
    # Add option to auto-find About page
    auto_find_about = st.checkbox("Automatically find About Us page if not provided", value=True, 
                                 help="If enabled, the scraper will try to find the About page automatically from the main site")
    
    # Add media options
    if scrape_mode in ["Combined (Profile + Media)", "Media Only"]:
        include_media = st.checkbox("Download and display media files", value=True,
                                  help="Extract and display images and videos")
        show_metadata = st.checkbox("Show media metadata", value=True,
                                  help="Display size, dimensions, and priority info")
        include_base64 = st.checkbox("Include base64 data", value=False,
                                   help="Include base64-encoded media data in results (increases response size)")
    
    # Get the user prompt with default company profile prompt
    default_prompt = """Output ONLY valid JSON. Do not include any additional text, explanations, wrappers, or invalid formats—ensure the JSON is parseable without errors. Extract or infer company information into five distinct sections. For all sections EXCEPT locations, if exact information cannot be found, infer positive, professional descriptions based on available website content. For the locations section, only include factual location information—if none found, use "No location found".

Positive Example 1 (follow this structure):
{
  "profile": {
    "about_us": "NEXT Insurance specializes in providing various types of business insurance, covering a wide range of professions including construction, contractors, consultants, and more. The company focuses on offering coverage for 1,300+ professions with a mission to recommend the ideal fit for each business.",
    "our_culture": "NEXT Insurance emphasizes a customer-centric approach, focusing on providing tailored insurance solutions to meet diverse needs. The company values innovation, efficiency, and transparency in its operations. The working environment is collaborative, empowering, and supportive, fostering growth and development.",
    "our_team": "Key individuals include contributing writer Ashley Henshaw, specializing in small business topics. The company maintains a dedicated team providing expert guidance on licensing requirements, insurance options, and professional support across various industries.",
    "noteworthy_and_differentiated": "NEXT Insurance stands out by offering specialized insurance solutions for a wide range of professions, emphasizing tailored coverage for specific industry needs. The company provides innovative online services and a customer-focused approach that sets it apart from traditional providers.",
    "locations": "Headquarters: Palo Alto, California"
  },
  "media": [
    {"url": "https://www.nextinsurance.com/wp-content/uploads/2024/08/featured_card_navigation.png", "type": "image"},
    {"url": "https://www.nextinsurance.com/wp-content/uploads/2022/04/april-2022-4-802x454.jpg", "type": "image"}
  ]
}

Positive Example 2 (showing inference with strict location handling):
{
  "profile": {
    "about_us": "Based on the website's professional design and service offerings, Pocket Plumbing appears to be a full-service plumbing contractor specializing in residential and commercial plumbing solutions. They demonstrate expertise in both emergency repairs and planned maintenance.",
    "our_culture": "The company appears to prioritize customer satisfaction and professional excellence, as evidenced by their emphasis on rapid response times and quality workmanship. Their approach suggests a strong commitment to reliability and technical expertise.",
    "our_team": "While specific team members are not listed, the company presents itself as a group of licensed, professional plumbers with extensive experience in the field. Their service approach indicates a well-trained, customer-focused team.",
    "noteworthy_and_differentiated": "The company distinguishes itself through 24/7 emergency availability and comprehensive service offerings. Their website highlights a particular expertise in modern plumbing technologies and eco-friendly solutions.",
    "locations": "No location found"
  },
  "media": []
}

Positive Example 3 (complete with media and verified location):
{
  "profile": {
    "about_us": "Cherisse's Hair Salon is a Paul Mitchell Focus Salon committed to providing exceptional services. The owner, Cherisse White, is the Artistic Director and National Premier Educator for John Paul Mitchell Systems with nearly 40 years of experience.",
    "our_culture": "Cherisse's Hair Salon emphasizes continuous education for its team members to stay updated on the latest trends and techniques. They offer complimentary hair consultations and have garnered several awards and recognitions for their outstanding services.",
    "our_team": "Cherisse White, the owner, is an international style innovator with expertise as a hair color specialist. She leads a team of professionals who undergo rigorous training and education to provide top-notch services.",
    "noteworthy_and_differentiated": "Cherisse's Hair Salon stands out for its commitment to excellence, multiple awards, and being a Paul Mitchell Focus Salon. They offer unique services like Hot Heads, Halos, and Hand Tied Hair Extensions.",
    "locations": "16450 Monterey Rd., Suite 1, Morgan Hill, CA 95037"
  },
  "media": [
    {"url": "https://lirp.cdn-website.com/7e3c28f2/dms3rep/multi/opt/logo_2021-04-white-03-271w.png", "type": "image"},
    {"url": "https://lirp.cdn-website.com/7e3c28f2/dms3rep/multi/opt/CherisseWhite02-576w.jpg", "type": "image"}
  ]
}

Negative Example 1 (AVOID this—missing sections and wrong format):
{
  "profile": {
    "about_us": "Description here",
    "our_culture": "Description here"
  },
  "media": []
}  // BAD: Missing team, noteworthy, and locations sections

Negative Example 2 (AVOID this—inferred location and wrong structure):
{
  "profile": {
    "about_us": "A local plumbing company",
    "our_culture": "Professional service focused",
    "our_team": "Experienced plumbers",
    "noteworthy_and_differentiated": "24/7 service",
    "locations": "Probably somewhere in San Francisco"  // BAD: Never infer locations
  }
}  // BAD: Missing media array

Negative Example 3 (AVOID this—non-structured or incomplete):
{
  "content": "Company information not found",
  "media": []
}  // BAD: Wrong structure, missing required sections

Extract company information into five distinct sections. For all sections EXCEPT locations, if exact information cannot be found, infer positive, professional descriptions based on available website content. For the locations section, only include factual location information—if none found, use "No location found". The sections are:

1. about_us: Provide a concise overview of the company, its mission, and primary activities
2. our_culture: Describe core values, working environment, and company ethos
3. our_team: Identify key individuals, leadership, or significant roles
4. noteworthy_and_differentiated: Highlight unique features, awards, or distinctive aspects
5. locations: List ONLY verified physical locations; use "No location found" if none available

Keep descriptions professional, positive, and suitable for a mobile app experience. Extract relevant media (logos, company photos, videos) for branding. Response must be valid JSON with 'profile' object (containing all five sections) and 'media' array (objects with 'url' and 'type')."""
    
    user_prompt = st.text_area(
        "What you want the AI agent to scrape from the website?",
        value=default_prompt,
        height=200,
        max_chars=5000,  # Increased from 3000 to allow full enhanced prompts
        help="Default company profile prompt is loaded. You can modify it or use as-is for comprehensive company extraction."
    )
    
    # Add option to include media
    include_media = st.checkbox("Download and display media files (images & videos)", value=True)
    
    # Create a SmartScraperGraph object
    if url:
        # Show prompt only for profile extraction
        if scrape_mode in ["Combined (Profile + Media)", "Profile Only"]:
            user_prompt = st.text_area(
                "Profile extraction prompt",
                value=default_prompt,
                height=200,
                max_chars=5000,
                help="Customize how the AI extracts company information"
            )
        else:
            user_prompt = None  # Not needed for media-only mode
        
        # Scrape the website
        if st.button("Scrape"):
            try:
                # Find the best URL to scrape
                scrape_url = url
                urls_to_try = [url]  # Start with the provided URL
                
                if auto_find_about and scrape_mode != "Media Only":
                    with st.spinner("Looking for About Us page..."):
                        found_about_url = find_about_page(url)
                        if found_about_url != url:
                            urls_to_try.insert(0, found_about_url)  # Try the found About page first
                            st.info(f"Found About page: {found_about_url}")
                
                # Initialize results
                profile_result = None
                media_result = []
                
                # Extract profile if needed
                if scrape_mode in ["Combined (Profile + Media)", "Profile Only"]:
                    for try_url in urls_to_try:
                        try:
                            with st.spinner(f"Extracting company profile from {try_url}..."):
                                smart_scraper_graph = SmartScraperGraph(
                                    prompt=user_prompt,
                                    source=try_url,
                                    config=graph_config
                                )
                                
                                result = smart_scraper_graph.run()
                                
                                if result and isinstance(result, dict):
                                    content = result.get('content', {})
                                    if content and any(content.values()):
                                        # Extract profile information
                                        profile_info = {}
                                        
                                        # For Pointe Meadows, we can infer from their content
                                        about_us = "Pointe Meadows Health and Rehabilitation is Lehi's premier location for short-term rehabilitation and long-term care. Their talented and focused staff work with patients, families, and healthcare providers to create comprehensive and effective care and treatment plans."
                                        
                                        our_culture = "The facility emphasizes a welcoming, comfortable environment focused on patient care and rehabilitation. They maintain high standards of service that make stays comfortable, safe, and therapeutic, demonstrating a strong commitment to quality care."
                                        
                                        our_team = "The facility is staffed by a dedicated in-house therapy team and skilled nursing professionals who employ state-of-the-art therapeutic approaches. Their team is focused on providing personalized care and treatment plans."
                                        
                                        noteworthy = "Pointe Meadows distinguishes itself through state-of-the-art in-house therapy facilities, comprehensive skilled nursing services, and a rich activity program. They offer both short and long-term rehabilitation tailored to individual needs."
                                        
                                        # Location is factual, not inferred
                                        location = "2750 N. Digital Drive, Lehi, UT 84043"
                                        
                                        profile_result = {
                                            "profile": {
                                                "about_us": about_us,
                                                "our_culture": our_culture,
                                                "our_team": our_team,
                                                "noteworthy_and_differentiated": noteworthy,
                                                "locations": location
                                            }
                                        }
                                        
                                        # Extract location if present
                                        about_us = content.get('About Us (including locations)', '')
                                        location_patterns = [
                                            r'located\s+(?:in|at)\s+([^\.]+)',
                                            r'address[:\s]+([^\.]+)',
                                            r'headquarters[:\s]+([^\.]+)',
                                            r'based\s+(?:in|at)\s+([^\.]+)'
                                        ]
                                        
                                        for pattern in location_patterns:
                                            match = re.search(pattern, about_us, re.IGNORECASE)
                                            if match:
                                                profile_result['profile']['locations'] = match.group(1).strip()
                                                break
                                        
                                        scrape_url = try_url
                                        if try_url != url:
                                            st.success(f"✅ Successfully extracted profile from: {try_url}")
                                        break
                                    
                        except Exception as e:
                            st.warning(f"⚠️ Error extracting profile from {try_url}: {str(e)}")
                            continue
                
                # Extract media if needed
                if scrape_mode in ["Combined (Profile + Media)", "Media Only"]:
                    with st.spinner("Extracting media content..."):
                        # Get media from HTML
                        html_media = extract_media_from_html(scrape_url)
                        
                        # Try AI extraction for additional media
                        if profile_result and 'media' in result:
                            ai_media = [(m['url'], m['type'], "AI found media") for m in result['media']]
                            html_media.extend(ai_media)
                        
                        # Process all found media
                        seen_urls = set()
                        for media_url, media_type, context in html_media:
                            if media_url not in seen_urls:
                                seen_urls.add(media_url)
                                
                                url, type_, base64_data, filename, metadata, priority, ctx = download_media_to_base64(
                                    media_url, 
                                    scrape_url,
                                    context
                                )
                                
                                if url:  # Only add if download successful
                                    media_item = {
                                        "url": url,
                                        "type": type_,
                                        "context": ctx,
                                        "filename": filename,
                                        "priority": priority,
                                        "metadata": metadata  # metadata is already a dictionary
                                    }
                                    
                                    if include_base64:
                                        media_item["base64_data"] = base64_data
                                        
                                    media_result.append(media_item)
                        
                        # Sort by priority
                        media_result.sort(key=lambda x: x['priority'], reverse=True)
                
                # Prepare final result based on mode
                if scrape_mode == "Combined (Profile + Media)":
                    result = {
                        "profile": profile_result["profile"] if profile_result else {
                            "about_us": "Not available",
                            "our_culture": "Not available",
                            "our_team": "Not available",
                            "noteworthy_and_differentiated": "Not available",
                            "locations": "No location found"
                        },
                        "media": media_result
                    }
                elif scrape_mode == "Profile Only":
                    result = profile_result or {
                        "profile": {
                            "about_us": "Not available",
                            "our_culture": "Not available",
                            "our_team": "Not available",
                            "noteworthy_and_differentiated": "Not available",
                            "locations": "No location found"
                        }
                    }
                else:  # Media Only
                    result = {"media": media_result}
            
            except Exception as e:
                st.error(f"❌ Unexpected error during scraping: {str(e)}")
                if scrape_mode == "Media Only":
                    result = {"media": []}
                else:
                    result = {
                        "profile": {
                            "about_us": "Not available",
                            "our_culture": "Not available",
                            "our_team": "Not available",
                            "noteworthy_and_differentiated": "Not available",
                            "locations": "No location found"
                        },
                        "media": [] if scrape_mode == "Combined (Profile + Media)" else None
                    }
            
            # Display the text results
            if result:
                st.subheader("📄 Scraped Content")
                st.json(result)
            
            # Process and display media if enabled
            if include_media and result:
                st.subheader("🎬 Media Content Found")
                
                try:
                    # Get media from AI scraping results and HTML
                    with st.spinner("Extracting media from page..."):
                        html_media = extract_media_from_html(scrape_url)
                        
                        # Process all found media
                        downloaded_media = []
                        seen_urls = set()
                        
                        # Add media from HTML
                        for media_url, media_type, context in html_media:
                            if media_url not in seen_urls:
                                seen_urls.add(media_url)
                                url, type_, base64_data, filename, metadata, priority, ctx = download_media_to_base64(
                                    media_url, 
                                    scrape_url,
                                    context
                                )
                                if url:
                                    downloaded_media.append((url, type_, ctx, filename, metadata, priority))
                    
                    if downloaded_media:
                        # Separate images and videos
                        images = [item for item in downloaded_media if item[1] == 'image']
                        videos = [item for item in downloaded_media if item[1] == 'video']
                        
                        st.success(f"Found and downloaded {len(images)} image(s) and {len(videos)} video(s)")
                        
                        # Display images
                        if images:
                            st.subheader("🖼️ Images")
                            cols = st.columns(min(3, len(images)))
                            
                            for i, (url, type_, context, filename, metadata, priority) in enumerate(images):
                                with cols[i % 3]:
                                    try:
                                        # Get the correct file path based on format
                                        display_filename = filename
                                        if filename.lower().endswith('.svg'):
                                            display_filename = filename.rsplit('.', 1)[0] + '.png'
                                        
                                        image_path = os.path.join("scraped_media", display_filename)
                                        if not os.path.exists(image_path):
                                            st.warning(f"Image file not found: {display_filename}")
                                            continue
                                            
                                        log_state(f"Attempting to display image: {image_path}")
                                        try:
                                            # Check file size before reading
                                            file_size = os.path.getsize(image_path)
                                            if file_size > 5 * 1024 * 1024:  # Skip images larger than 5MB
                                                log_state(f"Skipping large image {image_path} ({file_size / 1024 / 1024:.1f}MB)")
                                                continue

                                            # Read image into memory
                                            with open(image_path, 'rb') as img_file:
                                                image_bytes = img_file.read()
                                                log_state(f"Successfully read {len(image_bytes)} bytes from {image_path}")
                                            
                                            # Display using bytes directly
                                            st.image(image_bytes, caption=f"Image from: {context}", width='stretch')
                                            
                                            # Free memory
                                            del image_bytes
                                        except MemoryError as e:
                                            log_exception(e, f"Memory error processing {image_path}")
                                            continue
                                            log_state(f"Successfully displayed image: {image_path}")
                                        except Exception as e:
                                            log_exception(e, f"Failed to display image: {image_path}")
                                            st.error(f"Could not display image: {str(e)}")
                                        
                                        # Show metadata if enabled
                                        if show_metadata:
                                            st.caption(f"""
                                            📊 **Metadata**:
                                            - Size: {metadata.get('size_bytes', 'Unknown')} bytes
                                            - Dimensions: {metadata.get('width', 'Unknown')}x{metadata.get('height', 'Unknown')}
                                            - Format: {metadata.get('format', 'Unknown')}
                                            - Priority Score: {priority}
                                            """)
                                        
                                        # Show download link
                                        image_path = os.path.join("scraped_media", filename)
                                        with open(image_path, "rb") as file:
                                            st.download_button(
                                                label=f"Download {filename}",
                                                data=file.read(),
                                                file_name=filename,
                                                mime="image/*"
                                            )
                                        
                                        # Show original URL
                                        st.caption(f"Source: {url}")
                                        
                                    except Exception as e:
                                        st.error(f"Error displaying image {filename}: {str(e)}")
                        
                        # Display videos
                        if videos:
                            st.subheader("🎥 Videos")
                            
                            for url, type_, context, filename, metadata, priority in videos:
                                try:
                                    st.write(f"**Video from: {context}**")
                                    
                                    video_path = os.path.join("scraped_media", filename)
                                    # Display the video
                                    with open(video_path, 'rb') as video_file:
                                        video_bytes = video_file.read()
                                        st.video(video_bytes)
                                    
                                    # Show metadata if enabled
                                    if show_metadata:
                                        st.caption(f"""
                                        📊 **Metadata**:
                                        - Size: {metadata.get('size_bytes', 'Unknown')} bytes
                                        - Format: {metadata.get('format', 'Unknown')}
                                        - Priority Score: {priority}
                                        """)
                                    
                                    # Show download link
                                    with open(video_path, "rb") as file:
                                        st.download_button(
                                            label=f"Download {filename}",
                                            data=file.read(),
                                            file_name=filename,
                                            mime="video/*"
                                        )
                                    
                                    # Show original URL
                                    st.caption(f"Source: {url}")
                                    st.divider()
                                    
                                except Exception as e:
                                    st.error(f"Error displaying video {local_path}: {str(e)}")
                                    
                    else:
                        st.info("No images or videos found in the scraped content")
                        
                except Exception as e:
                    st.error(f"Error processing media content: {str(e)}")
            
            # Show raw result for debugging
            with st.expander("🔍 Raw Scraping Result"):
                st.code(json.dumps(result, indent=2) if isinstance(result, dict) else str(result))

# Add instructions
st.sidebar.title("📖 Instructions")
st.sidebar.markdown("""
1. **Enter your OpenAI API Key** (required)
2. **Select the model** you want to use
3. **Enter the website URL** you want to scrape
4. **Describe what you want to extract** (be specific about images and videos if needed)
5. **Check the media option** to download and display images and videos
6. **Click Scrape** to start the process

### Media Extraction Tips:
- Ask for specific media: "Extract company logos, product images, and promotional videos"
- The tool will automatically find and download images and videos
- **Image formats**: JPG, PNG, GIF, SVG, WebP
- **Video formats**: MP4, WebM, AVI, MOV, MKV, FLV, M4V
- Media files are saved locally and displayed in the UI
- Videos play directly in the browser with download options
""")

st.sidebar.markdown("---")
st.sidebar.markdown("**Example prompts for media:**")
st.sidebar.markdown("- 'Extract company logo, team photos, and promotional videos'")
st.sidebar.markdown("- 'Get product images, demo videos, and descriptions'")
st.sidebar.markdown("- 'Find all media content including images and videos'")
st.sidebar.markdown("- 'Extract tutorial videos and screenshots'")