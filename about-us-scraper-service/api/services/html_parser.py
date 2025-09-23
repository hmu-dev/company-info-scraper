"""HTML parsing service for extracting media content."""

from typing import List, Tuple
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin


def extract_media_from_html(url: str) -> List[Tuple[str, str, str]]:
    """
    Extract media content from HTML.

    Args:
        url: The URL to scrape

    Returns:
        List of tuples containing (url, type, context)
    """
    # Get HTML content
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    media_items = []

    # Extract images
    for img in soup.find_all("img"):
        src = img.get("src")
        if src:
            # Make URL absolute
            src = urljoin(url, src)

            # Get context from alt text, title, or parent text
            parent_text = img.parent.get_text(strip=True)[:100] if img.parent else None
            context = (
                img.get("alt")
                or img.get("title")
                or (
                    parent_text
                    if parent_text and parent_text != str(img.get("src", ""))
                    else None
                )
                or "Image"
            )

            media_items.append((src, "image", context))

    # Extract videos
    for video in soup.find_all(["video", "iframe"]):
        src = video.get("src")
        if src:
            # Make URL absolute
            src = urljoin(url, src)

            # Get context from title or parent text
            context = video.get("title") or "Video"

            media_items.append((src, "video", context))

    return media_items
