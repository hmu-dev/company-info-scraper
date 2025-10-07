"""
Video Thumbnail Extraction and Generation Utilities

This module handles video thumbnail extraction, including:
- Extracting existing poster/thumbnail URLs from video elements
- Generating placeholder thumbnails for protected videos
- Extracting thumbnails from common video platforms (YouTube, Vimeo)
- Creating fallback placeholder system
"""

import base64
import hashlib
import re
from io import BytesIO
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse, parse_qs

from PIL import Image, ImageDraw, ImageFont
import requests


class VideoThumbnailExtractor:
    """Extract and generate video thumbnails with multiple fallback strategies"""
    
    def __init__(self, default_width: int = 320, default_height: int = 180):
        self.default_width = default_width
        self.default_height = default_height
        self.placeholder_cache = {}
    
    def extract_video_thumbnails(
        self, 
        video_elements: List[Dict], 
        base_url: str
    ) -> List[Dict[str, str]]:
        """
        Extract thumbnails from video elements with multiple strategies
        
        Args:
            video_elements: List of video element data
            base_url: Base URL for resolving relative URLs
            
        Returns:
            List of thumbnail dictionaries with url, type, and source info
        """
        thumbnails = []
        
        for video in video_elements:
            video_url = video.get('url', '')
            video_type = video.get('type', 'video')
            
            # Strategy 1: Use existing poster attribute
            poster_url = video.get('poster', '')
            if poster_url:
                full_poster_url = self._resolve_url(poster_url, base_url)
                thumbnails.append({
                    'video_url': video_url,
                    'thumbnail_url': full_poster_url,
                    'thumbnail_type': 'poster',
                    'source': 'existing_poster',
                    'width': self.default_width,
                    'height': self.default_height
                })
                continue
            
            # Strategy 2: Extract from video platform URLs
            platform_thumbnail = self._extract_platform_thumbnail(video_url)
            if platform_thumbnail:
                thumbnails.append({
                    'video_url': video_url,
                    'thumbnail_url': platform_thumbnail,
                    'thumbnail_type': 'platform',
                    'source': self._get_platform_name(video_url),
                    'width': self.default_width,
                    'height': self.default_height
                })
                continue
            
            # Strategy 3: Try to extract from video metadata (if accessible)
            accessible_thumbnail = self._try_extract_video_metadata_thumbnail(video_url)
            if accessible_thumbnail:
                thumbnails.append({
                    'video_url': video_url,
                    'thumbnail_url': accessible_thumbnail,
                    'thumbnail_type': 'metadata',
                    'source': 'video_metadata',
                    'width': self.default_width,
                    'height': self.default_height
                })
                continue
            
            # Strategy 4: Generate placeholder thumbnail
            placeholder_thumbnail = self._generate_placeholder_thumbnail(video_url, video_type)
            thumbnails.append({
                'video_url': video_url,
                'thumbnail_url': placeholder_thumbnail,
                'thumbnail_type': 'placeholder',
                'source': 'generated',
                'width': self.default_width,
                'height': self.default_height,
                'is_placeholder': True
            })
        
        return thumbnails
    
    def _resolve_url(self, url: str, base_url: str) -> str:
        """Resolve relative URLs to absolute URLs"""
        if url.startswith(('http://', 'https://')):
            return url
        
        # Simple URL joining
        if base_url.endswith('/'):
            return base_url + url.lstrip('/')
        else:
            return base_url + '/' + url.lstrip('/')
    
    def _extract_platform_thumbnail(self, video_url: str) -> Optional[str]:
        """Extract thumbnail from common video platforms"""
        try:
            parsed_url = urlparse(video_url)
            
            # YouTube
            if 'youtube.com' in parsed_url.netloc or 'youtu.be' in parsed_url.netloc:
                video_id = self._extract_youtube_id(video_url)
                if video_id:
                    return f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
            
            # Vimeo
            elif 'vimeo.com' in parsed_url.netloc:
                video_id = self._extract_vimeo_id(video_url)
                if video_id:
                    # Try to get thumbnail from Vimeo API (requires API key in production)
                    return f"https://vumbnail.com/{video_id}.jpg"
            
            # Dailymotion
            elif 'dailymotion.com' in parsed_url.netloc:
                video_id = self._extract_dailymotion_id(video_url)
                if video_id:
                    return f"https://www.dailymotion.com/thumbnail/video/{video_id}"
            
            # Wistia
            elif 'wistia.com' in parsed_url.netloc or 'wistia.net' in parsed_url.netloc:
                video_id = self._extract_wistia_id(video_url)
                if video_id:
                    return f"https://fast.wistia.com/embed/medias/{video_id}/swatch"
            
        except Exception:
            pass
        
        return None
    
    def _extract_youtube_id(self, url: str) -> Optional[str]:
        """Extract YouTube video ID from URL"""
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com/embed/([a-zA-Z0-9_-]{11})',
            r'youtube\.com/v/([a-zA-Z0-9_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_vimeo_id(self, url: str) -> Optional[str]:
        """Extract Vimeo video ID from URL"""
        patterns = [
            r'vimeo\.com/(\d+)',
            r'player\.vimeo\.com/video/(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_dailymotion_id(self, url: str) -> Optional[str]:
        """Extract Dailymotion video ID from URL"""
        pattern = r'dailymotion\.com/video/([a-zA-Z0-9]+)'
        match = re.search(pattern, url)
        return match.group(1) if match else None
    
    def _extract_wistia_id(self, url: str) -> Optional[str]:
        """Extract Wistia video ID from URL"""
        pattern = r'wistia\.(?:com|net)/(?:medias|embed)/([a-zA-Z0-9]+)'
        match = re.search(pattern, url)
        return match.group(1) if match else None
    
    def _get_platform_name(self, url: str) -> str:
        """Get platform name from URL"""
        if 'youtube.com' in url or 'youtu.be' in url:
            return 'youtube'
        elif 'vimeo.com' in url:
            return 'vimeo'
        elif 'dailymotion.com' in url:
            return 'dailymotion'
        elif 'wistia.com' in url or 'wistia.net' in url:
            return 'wistia'
        else:
            return 'unknown'
    
    def _try_extract_video_metadata_thumbnail(self, video_url: str) -> Optional[str]:
        """Try to extract thumbnail from video metadata (if accessible)"""
        try:
            # This would require downloading the video file to extract metadata
            # For protected videos (like CloudFront), this will likely fail
            # We'll implement a simple check without downloading the full file
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                'Range': 'bytes=0-1023'  # Only request first 1KB to check accessibility
            }
            
            response = requests.head(video_url, headers=headers, timeout=5)
            
            # If we can't even do a HEAD request, the video is likely protected
            if response.status_code in [403, 404, 405]:
                return None
            
            # For now, return None since we can't extract metadata without downloading
            # In a full implementation, you might try to extract thumbnail from video headers
            return None
            
        except Exception:
            return None
    
    def _generate_placeholder_thumbnail(
        self, 
        video_url: str, 
        video_type: str = 'video'
    ) -> str:
        """Generate a placeholder thumbnail for videos"""
        # Create a cache key based on video URL
        cache_key = hashlib.md5(video_url.encode()).hexdigest()
        
        if cache_key in self.placeholder_cache:
            return self.placeholder_cache[cache_key]
        
        try:
            # Create a placeholder image
            img = Image.new('RGB', (self.default_width, self.default_height), color='#2c3e50')
            draw = ImageDraw.Draw(img)
            
            # Try to load a font (fallback to default if not available)
            try:
                font_large = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 24)
                font_small = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 14)
            except:
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Draw play button
            button_size = 60
            button_x = (self.default_width - button_size) // 2
            button_y = (self.default_height - button_size) // 2
            
            # Draw circle for play button
            draw.ellipse(
                [button_x, button_y, button_x + button_size, button_y + button_size],
                fill='#3498db',
                outline='#2980b9',
                width=3
            )
            
            # Draw triangle play icon
            triangle_points = [
                (button_x + 20, button_y + 15),
                (button_x + 20, button_y + 45),
                (button_x + 45, button_y + 30)
            ]
            draw.polygon(triangle_points, fill='white')
            
            # Add text
            text = "Video"
            if video_type == 'iframe':
                text = "Embedded Video"
            
            # Get text bounding box
            bbox = draw.textbbox((0, 0), text, font=font_small)
            text_width = bbox[2] - bbox[0]
            text_x = (self.default_width - text_width) // 2
            text_y = button_y + button_size + 10
            
            draw.text((text_x, text_y), text, fill='white', font=font_small)
            
            # Add "Protected" indicator
            protected_text = "Protected Content"
            bbox = draw.textbbox((0, 0), protected_text, font=font_small)
            protected_width = bbox[2] - bbox[0]
            protected_x = (self.default_width - protected_width) // 2
            protected_y = text_y + 20
            
            draw.text((protected_x, protected_y), protected_text, fill='#e74c3c', font=font_small)
            
            # Convert to base64 data URL
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_data = buffer.getvalue()
            img_base64 = base64.b64encode(img_data).decode()
            
            data_url = f"data:image/png;base64,{img_base64}"
            
            # Cache the result
            self.placeholder_cache[cache_key] = data_url
            
            return data_url
            
        except Exception:
            # Fallback to a simple colored rectangle
            return f"data:image/svg+xml;base64,{base64.b64encode(f'''
                <svg width="{self.default_width}" height="{self.default_height}" xmlns="http://www.w3.org/2000/svg">
                    <rect width="100%" height="100%" fill="#2c3e50"/>
                    <circle cx="{self.default_width//2}" cy="{self.default_height//2}" r="30" fill="#3498db"/>
                    <polygon points="{self.default_width//2-10},{self.default_height//2-15} {self.default_width//2-10},{self.default_height//2+15} {self.default_width//2+15},{self.default_height//2}" fill="white"/>
                    <text x="{self.default_width//2}" y="{self.default_height//2+40}" text-anchor="middle" fill="white" font-family="Arial" font-size="12">Video</text>
                </svg>
            '''.encode()).decode()}"


def extract_video_thumbnails_from_soup(
    soup, 
    base_url: str
) -> List[Dict[str, str]]:
    """
    Extract video thumbnails from BeautifulSoup object
    
    Args:
        soup: BeautifulSoup object
        base_url: Base URL for resolving relative URLs
        
    Returns:
        List of thumbnail dictionaries
    """
    extractor = VideoThumbnailExtractor()
    
    # Find all video elements
    video_elements = []
    
    # HTML5 video elements
    for video in soup.find_all('video'):
        video_elements.append({
            'url': video.get('src', ''),
            'type': 'video',
            'poster': video.get('poster', ''),
            'title': video.get('title', '')
        })
    
    # iframe elements (embedded videos)
    for iframe in soup.find_all('iframe'):
        src = iframe.get('src', '')
        if any(platform in src.lower() for platform in ['youtube', 'vimeo', 'dailymotion', 'wistia']):
            video_elements.append({
                'url': src,
                'type': 'iframe',
                'poster': iframe.get('poster', ''),
                'title': iframe.get('title', '')
            })
    
    return extractor.extract_video_thumbnails(video_elements, base_url)
