# Import the required libraries
import streamlit as st
import requests
import os
import json
from urllib.parse import urljoin, urlparse
from scrapegraphai.graphs import SmartScraperGraph
import base64
from io import BytesIO
from PIL import Image
from bs4 import BeautifulSoup
import re

# Set up the Streamlit app
st.title("Web Scrapping AI Agent 🕵️‍♂️")
st.caption("This app allows you to scrape a website using OpenAI API and display media content")

# Add custom CSS for expandable text area
st.markdown("""
<style>
    .stTextArea > div > div > textarea {
        resize: vertical;
        min-height: 150px;
        max-height: 400px;
        overflow-y: auto;
    }
</style>
""", unsafe_allow_html=True)

# Create media directory if it doesn't exist
if not os.path.exists("scraped_media"):
    os.makedirs("scraped_media")

def download_media(media_url, base_url, session=None):
    """Download media (image or video) from URL and return the local path"""
    try:
        # Handle relative URLs
        if not media_url.startswith(('http://', 'https://')):
            media_url = urljoin(base_url, media_url)
        
        # Use session if provided, otherwise create a new request
        if session:
            response = session.get(media_url, timeout=30, stream=True)
        else:
            response = requests.get(media_url, timeout=30, stream=True)
        
        if response.status_code == 200:
            # Get file extension from URL
            parsed_url = urlparse(media_url)
            file_name = os.path.basename(parsed_url.path)
            
            # Determine file type and set appropriate extension
            content_type = response.headers.get('content-type', '').lower()
            if not file_name or '.' not in file_name:
                if 'video' in content_type:
                    if 'mp4' in content_type:
                        file_name = f"video_{hash(media_url) % 10000}.mp4"
                    elif 'webm' in content_type:
                        file_name = f"video_{hash(media_url) % 10000}.webm"
                    elif 'avi' in content_type:
                        file_name = f"video_{hash(media_url) % 10000}.avi"
                    else:
                        file_name = f"video_{hash(media_url) % 10000}.mp4"
                else:
                    file_name = f"image_{hash(media_url) % 10000}.jpg"
            
            # Save the media file
            file_path = os.path.join("scraped_media", file_name)
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Determine media type
            file_ext = file_name.lower().split('.')[-1]
            media_type = 'video' if file_ext in ['mp4', 'webm', 'avi', 'mov', 'mkv', 'flv', 'm4v'] else 'image'
            
            return file_path, media_url, media_type
    except Exception as e:
        st.warning(f"Could not download media from {media_url}: {str(e)}")
    
    return None, media_url, 'unknown'

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

# Get OpenAI API key from user
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
    # Get the URL of the website to scrape
    url = st.text_input("Enter the URL of the website you want to scrape")
    
    # Add option to auto-find About page
    auto_find_about = st.checkbox("Automatically find About Us page if not provided", value=True, 
                                 help="If enabled, the scraper will try to find the About page automatically from the main site")
    
    # Get the user prompt
    user_prompt = st.text_area(
        "What you want the AI agent to scrape from the website?",
        height=150,
        max_chars=2000,
        help="Describe what you want to extract. Be specific about text, images, or data you're looking for."
    )
    
    # Add option to include media
    include_media = st.checkbox("Download and display media files (images & videos)", value=True)
    
    # Create a SmartScraperGraph object
    if url and user_prompt:
        smart_scraper_graph = SmartScraperGraph(
            prompt=user_prompt,
            source=url,
            config=graph_config
        )
        
        # Scrape the website
        if st.button("Scrape"):
            try:
                # Find the best URL to scrape
                scrape_url = url
                urls_to_try = [url]  # Start with the provided URL
                
                if auto_find_about:
                    with st.spinner("Looking for About Us page..."):
                        found_about_url = find_about_page(url)
                        if found_about_url != url:
                            urls_to_try.insert(0, found_about_url)  # Try the found About page first
                            st.info(f"Found About page: {found_about_url}")
                
                # Try scraping multiple URLs until we get good results
                result = None
                successful_url = None
                
                for try_url in urls_to_try:
                    try:
                        with st.spinner(f"Scraping content from {try_url}..."):
                            # Create scraper for this URL
                            smart_scraper_graph = SmartScraperGraph(
                                prompt=user_prompt + "\n\nIMPORTANT: If you find any image URLs, video URLs, or media content, please include them in your response with clear labels like 'image:', 'video:', 'logo:', etc.",
                                source=try_url,
                                config=graph_config
                            )
                            
                            result = smart_scraper_graph.run()
                            
                            # Check if we got meaningful results
                            if result and (isinstance(result, dict) or (isinstance(result, str) and len(result) > 100)):
                                successful_url = try_url
                                scrape_url = try_url
                                if try_url != url:
                                    st.success(f"✅ Successfully scraped from: {try_url}")
                                break
                            else:
                                st.warning(f"⚠️ Limited content found at {try_url}, trying alternative...")
                                
                    except Exception as e:
                        st.warning(f"⚠️ Error scraping {try_url}: {str(e)}")
                        continue
                
                if not result or not successful_url:
                    st.error("❌ Could not extract meaningful content from any of the attempted URLs. Please try a different URL or check if the website is accessible.")
                    # Still try to extract media even if AI scraping failed
                    scrape_url = urls_to_try[0]
                    result = {"content": "Content extraction failed, but attempting media extraction..."}
            
            except Exception as e:
                st.error(f"❌ Unexpected error during scraping: {str(e)}")
                st.error("This might be due to the website structure or connectivity issues. Trying media extraction only...")
                scrape_url = url
                result = {"content": "AI scraping failed, but attempting media extraction..."}
            
            # Display the text results
            if result:
                st.subheader("📄 Scraped Content")
                st.json(result)
            
            # Process and display media if enabled
            if include_media and result:
                st.subheader("🎬 Media Content Found")
                
                try:
                    # Get media from AI scraping results
                    downloaded_media = display_media_content(result, scrape_url)
                    
                    # Also extract media directly from HTML
                    with st.spinner("Extracting media from page..."):
                        html_media = extract_media_from_html(scrape_url)
                        
                        # Download HTML-found media
                        for media_url, media_type, context in html_media:
                            local_path, original_url, detected_type = download_media(media_url, scrape_url)
                            if local_path:
                                downloaded_media.append((local_path, original_url, context, detected_type))
                    
                    if downloaded_media:
                        # Separate images and videos
                        images = [item for item in downloaded_media if item[3] == 'image']
                        videos = [item for item in downloaded_media if item[3] == 'video']
                        
                        st.success(f"Found and downloaded {len(images)} image(s) and {len(videos)} video(s)")
                        
                        # Display images
                        if images:
                            st.subheader("🖼️ Images")
                            cols = st.columns(min(3, len(images)))
                            
                            for i, (local_path, original_url, context, media_type) in enumerate(images):
                                with cols[i % 3]:
                                    try:
                                        # Display the image
                                        image = Image.open(local_path)
                                        st.image(image, caption=f"Image from: {context}", use_column_width=True)
                                        
                                        # Show download link
                                        with open(local_path, "rb") as file:
                                            st.download_button(
                                                label=f"Download {os.path.basename(local_path)}",
                                                data=file.read(),
                                                file_name=os.path.basename(local_path),
                                                mime="image/*"
                                            )
                                        
                                        # Show original URL
                                        st.caption(f"Source: {original_url}")
                                        
                                    except Exception as e:
                                        st.error(f"Error displaying image {local_path}: {str(e)}")
                        
                        # Display videos
                        if videos:
                            st.subheader("🎥 Videos")
                            
                            for local_path, original_url, context, media_type in videos:
                                try:
                                    st.write(f"**Video from: {context}**")
                                    
                                    # Display the video
                                    with open(local_path, 'rb') as video_file:
                                        video_bytes = video_file.read()
                                        st.video(video_bytes)
                                    
                                    # Show download link
                                    with open(local_path, "rb") as file:
                                        st.download_button(
                                            label=f"Download {os.path.basename(local_path)}",
                                            data=file.read(),
                                            file_name=os.path.basename(local_path),
                                            mime="video/*"
                                        )
                                    
                                    # Show original URL
                                    st.caption(f"Source: {original_url}")
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