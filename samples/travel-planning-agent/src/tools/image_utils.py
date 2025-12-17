"""
Image Utilities for Travel Planning Agent
Downloads images from URLs and converts them to base64 for embedding in responses
"""

import base64
import io
import hashlib
from typing import Optional, Dict
from urllib.parse import urlparse

import requests
from PIL import Image


class ImageCache:
    """Simple in-memory cache for base64 encoded images"""
    _cache: Dict[str, str] = {}

    @classmethod
    def get(cls, url: str) -> Optional[str]:
        """Get cached base64 image by URL"""
        key = cls._hash_url(url)
        return cls._cache.get(key)

    @classmethod
    def set(cls, url: str, base64_data: str) -> None:
        """Cache base64 image by URL"""
        key = cls._hash_url(url)
        cls._cache[key] = base64_data

    @classmethod
    def _hash_url(cls, url: str) -> str:
        """Create a hash key from URL"""
        return hashlib.md5(url.encode()).hexdigest()

    @classmethod
    def clear(cls) -> None:
        """Clear the cache"""
        cls._cache.clear()


def download_and_encode_base64(
    url: str,
    max_width: int = 400,
    max_height: int = 300,
    quality: int = 70,
    timeout: int = 10
) -> Optional[str]:
    """
    Download an image from URL, resize it, and return as base64 data URI.

    Args:
        url: Image URL to download
        max_width: Maximum width to resize to (maintains aspect ratio)
        max_height: Maximum height to resize to (maintains aspect ratio)
        quality: JPEG quality (1-100)
        timeout: Request timeout in seconds

    Returns:
        Base64 data URI string (e.g., "data:image/jpeg;base64,/9j/...")
        or None if download/processing fails
    """
    if not url:
        return None

    # Check cache first
    cached = ImageCache.get(url)
    if cached:
        return cached

    try:
        # Download the image
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; TravelPlanningAgent/1.0)'
        }
        response = requests.get(url, headers=headers, timeout=timeout, stream=True)
        response.raise_for_status()

        # Check content type
        content_type = response.headers.get('content-type', '')
        if not content_type.startswith('image/'):
            print(f"  Not an image: {content_type}")
            return None

        # Load image
        image_data = response.content
        image = Image.open(io.BytesIO(image_data))

        # Convert to RGB if necessary (for JPEG output)
        if image.mode in ('RGBA', 'P', 'LA'):
            # Create white background for transparent images
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'P':
                image = image.convert('RGBA')
            background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
            image = background
        elif image.mode != 'RGB':
            image = image.convert('RGB')

        # Resize maintaining aspect ratio
        image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

        # Save to bytes as JPEG
        buffer = io.BytesIO()
        image.save(buffer, format='JPEG', quality=quality, optimize=True)
        buffer.seek(0)

        # Encode to base64
        base64_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
        data_uri = f"data:image/jpeg;base64,{base64_data}"

        # Cache the result
        ImageCache.set(url, data_uri)

        return data_uri

    except requests.RequestException as e:
        print(f"  Failed to download image from {url}: {str(e)}")
        return None
    except Exception as e:
        print(f"  Failed to process image from {url}: {str(e)}")
        return None


def create_placeholder_svg(
    label: str,
    width: int = 400,
    height: int = 300,
    bg_color: str = "#e0e0e0",
    text_color: str = "#666666"
) -> str:
    """
    Create a simple SVG placeholder image as base64 data URI.

    Args:
        label: Text to display on the placeholder
        width: SVG width
        height: SVG height
        bg_color: Background color
        text_color: Text color

    Returns:
        Base64 data URI string for SVG image
    """
    # Escape special characters in label
    label = label.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    # Truncate long labels
    if len(label) > 30:
        label = label[:27] + "..."

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect fill="{bg_color}" width="{width}" height="{height}"/>
  <text fill="{text_color}" font-family="Arial, sans-serif" font-size="16" text-anchor="middle" x="{width//2}" y="{height//2}">{label}</text>
  <text fill="{text_color}" font-family="Arial, sans-serif" font-size="12" text-anchor="middle" x="{width//2}" y="{height//2 + 20}">Image Placeholder</text>
</svg>'''

    base64_data = base64.b64encode(svg.encode('utf-8')).decode('utf-8')
    return f"data:image/svg+xml;base64,{base64_data}"


def get_image_from_urls(
    urls: list,
    max_width: int = 400,
    max_height: int = 300,
    fallback_label: str = "Image"
) -> Optional[str]:
    """
    Try to get a base64 image from a list of URLs, with fallback to placeholder.

    Args:
        urls: List of image URLs to try (in order of preference)
        max_width: Maximum width for downloaded images
        max_height: Maximum height for downloaded images
        fallback_label: Label for placeholder if all URLs fail

    Returns:
        Base64 data URI string (either from URL or placeholder)
    """
    for url in urls:
        if url:
            result = download_and_encode_base64(url, max_width, max_height)
            if result:
                return result

    # Return placeholder if all URLs failed
    return create_placeholder_svg(fallback_label, max_width, max_height)
