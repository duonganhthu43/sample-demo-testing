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


# Cache for item-specific image searches
_item_image_cache: Dict[str, Optional[str]] = {}

# Global set to track used image hashes - prevents same image from being used for different items
_used_image_hashes: set = set()


def get_image_hash(base64_data: str) -> str:
    """Get a hash of the image for deduplication (first 100 chars of base64 is enough)"""
    if not base64_data:
        return ""
    # Skip the data:image/jpeg;base64, prefix to get actual image data
    if "base64," in base64_data:
        base64_data = base64_data.split("base64,", 1)[1]
    return base64_data[:100]


def is_image_used(base64_data: str) -> bool:
    """Check if this image has already been used for another item"""
    img_hash = get_image_hash(base64_data)
    return img_hash in _used_image_hashes


def mark_image_used(base64_data: str) -> None:
    """Mark an image as used so it won't be assigned to other items"""
    img_hash = get_image_hash(base64_data)
    if img_hash:
        _used_image_hashes.add(img_hash)


def clear_used_images() -> None:
    """Clear the used images tracker (call at start of new planning session)"""
    _used_image_hashes.clear()


def search_images_parallel(
    items: list,
    destination: str,
    tavily_api_key: str,
    item_type: str = "activity",
    max_workers: int = 5,
    max_width: int = 400,
    max_height: int = 300
) -> Dict[str, Optional[str]]:
    """
    Search for images for multiple items in parallel.

    Args:
        items: List of dicts with 'name' key (e.g., hotels, restaurants, activities)
        destination: Destination city/location for context
        tavily_api_key: Tavily API key
        item_type: Type of item ("restaurant", "hotel", "activity", "attraction")
        max_workers: Maximum concurrent threads (default 5)
        max_width: Maximum width for downloaded images
        max_height: Maximum height for downloaded images

    Returns:
        Dict mapping item name to base64 data URI (or None if not found)
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    results: Dict[str, Optional[str]] = {}
    items_to_search = []

    # Filter items that need image search
    for item in items:
        name = item.get("name", "")
        if not name:
            continue
        # Check cache first
        cache_key = f"{name.lower()}_{destination.lower()}_{item_type}"
        if cache_key in _item_image_cache:
            results[name] = _item_image_cache[cache_key]
        else:
            items_to_search.append(item)

    if not items_to_search:
        return results

    print(f"  Searching images for {len(items_to_search)} {item_type}s in parallel...")

    def search_single(item: Dict) -> tuple:
        name = item.get("name", "")
        base64_img = search_image_for_item(
            item_name=name,
            item_type=item_type,
            destination=destination,
            tavily_api_key=tavily_api_key,
            max_width=max_width,
            max_height=max_height
        )
        return name, base64_img

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(search_single, item): item for item in items_to_search}

        for future in as_completed(futures):
            try:
                name, base64_img = future.result()
                results[name] = base64_img
                if base64_img:
                    print(f"    Found image for {name}")
            except Exception as e:
                item = futures[future]
                print(f"    Image search failed for {item.get('name', 'unknown')}: {e}")
                results[item.get("name", "")] = None

    return results


def search_image_for_item(
    item_name: str,
    item_type: str,
    destination: str,
    tavily_api_key: str,
    max_width: int = 400,
    max_height: int = 300
) -> Optional[str]:
    """
    Search for a specific image for an item using Tavily API.

    Args:
        item_name: Name of the item (e.g., "Hajime Restaurant", "Tokyo Tower")
        item_type: Type of item ("restaurant", "hotel", "activity", "attraction")
        destination: Destination city/location for context
        tavily_api_key: Tavily API key
        max_width: Maximum width for downloaded images
        max_height: Maximum height for downloaded images

    Returns:
        Base64 data URI string or None if search fails
    """
    # Create cache key
    cache_key = f"{item_name.lower()}_{destination.lower()}_{item_type}"

    if cache_key in _item_image_cache:
        return _item_image_cache[cache_key]

    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=tavily_api_key)

        # Build a targeted search query for the specific item
        if item_type == "restaurant":
            query = f"{item_name} restaurant {destination} interior food photo"
        elif item_type == "hotel":
            query = f"{item_name} hotel {destination} exterior building photo"
        elif item_type in ["activity", "attraction"]:
            query = f"{item_name} {destination} tourist attraction photo"
        else:
            query = f"{item_name} {destination} photo"

        # Search with include_images=True
        response = client.search(
            query=query,
            max_results=3,
            search_depth="basic",
            include_images=True
        )

        # Get images from response
        images = response.get("images", [])

        # Try each image URL until one works (that hasn't been used already)
        for img in images:
            url = img if isinstance(img, str) else img.get("url", "")
            if url and _is_likely_photo(url):
                base64_img = download_and_encode_base64(url, max_width, max_height)
                if base64_img:
                    # Check if this image was already used for another item
                    if is_image_used(base64_img):
                        print(f"    Skipping duplicate image for {item_name}")
                        continue  # Try next image
                    mark_image_used(base64_img)
                    _item_image_cache[cache_key] = base64_img
                    return base64_img

        # If no filtered images worked, try any image
        for img in images:
            url = img if isinstance(img, str) else img.get("url", "")
            if url:
                base64_img = download_and_encode_base64(url, max_width, max_height)
                if base64_img:
                    # Check if this image was already used for another item
                    if is_image_used(base64_img):
                        print(f"    Skipping duplicate image for {item_name}")
                        continue  # Try next image
                    mark_image_used(base64_img)
                    _item_image_cache[cache_key] = base64_img
                    return base64_img

        _item_image_cache[cache_key] = None
        return None

    except Exception as e:
        print(f"  Item image search failed for '{item_name}': {str(e)}")
        _item_image_cache[cache_key] = None
        return None


def _is_likely_photo(url: str) -> bool:
    """
    Filter out URLs that are unlikely to be relevant photos.
    Returns True if the URL seems like a real photo.
    """
    url_lower = url.lower()

    # Skip common non-photo patterns
    skip_patterns = [
        'anime', 'cartoon', 'manga', 'illustration',
        'avatar', 'icon', 'logo', 'badge',
        'emoji', 'sticker', 'clipart',
        'pixiv', 'deviantart', 'artstation',
        'pinterest.com/pin',  # Pinterest pins often aren't the actual image
        'facebook.com', 'twitter.com', 'x.com',
        'gravatar', 'profile', 'user_avatar',
    ]

    for pattern in skip_patterns:
        if pattern in url_lower:
            return False

    # Prefer URLs from known photo/travel sources
    good_sources = [
        'tripadvisor', 'booking.com', 'hotels.com',
        'expedia', 'agoda', 'yelp',
        'unsplash', 'pexels', 'shutterstock',
        'gettyimages', 'istockphoto',
        'wikimedia', 'wikipedia',
        'cloudfront', 'amazonaws',
        'googleusercontent',
    ]

    # If from a known good source, accept it
    for source in good_sources:
        if source in url_lower:
            return True

    # Accept common image extensions
    if any(ext in url_lower for ext in ['.jpg', '.jpeg', '.png', '.webp']):
        return True

    return True  # Default to accepting if no red flags
