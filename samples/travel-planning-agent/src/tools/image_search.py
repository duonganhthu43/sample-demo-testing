"""
Image Search Tool for Travel Planning Agent
Searches for specific images based on query and returns base64 encoded data
"""

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional

from .image_utils import (
    download_and_encode_base64,
    ImageCache,
    simplify_query,
    is_image_url_used,
    mark_image_url_used
)


class ImageSearchTool:
    """
    Tool for searching and downloading specific images.
    Uses Tavily API to find relevant images based on search queries.
    """

    def __init__(self, config=None):
        from ..utils.config import get_config
        self.config = config or get_config()
        self._cache: Dict[str, str] = {}

    def search_image(
        self,
        query: str,
        destination: str = "",
        max_width: int = 600,
        max_height: int = 400,
        category: str = ""
    ) -> Optional[str]:
        """
        Search for a specific image and return as base64.

        Args:
            query: Image search query (e.g., "Sensoji Temple")
            destination: Optional destination context (e.g., "Tokyo")
            max_width: Maximum image width
            max_height: Maximum image height
            category: Optional category hint (restaurant, attraction, hotel)

        Returns:
            Base64 data URI or None if not found
        """
        # Build optimized search query based on category
        search_queries = self._build_search_queries(query, destination, category)

        # Check cache first
        for search_query in search_queries:
            cache_key = search_query.lower()
            if cache_key in self._cache:
                return self._cache[cache_key]

        # Try each query variant until we find an image
        for search_query in search_queries:
            image_urls = self._search_tavily(search_query)
            for image_url in image_urls:
                # Check URL deduplication before downloading
                if is_image_url_used(image_url):
                    print(f"  Skipping duplicate URL: {image_url[:50]}...")
                    continue
                base64_data = download_and_encode_base64(
                    image_url,
                    max_width=max_width,
                    max_height=max_height
                )
                if base64_data:
                    mark_image_url_used(image_url)
                    # Cache with primary query key
                    self._cache[search_queries[0].lower()] = base64_data
                    return base64_data

        # Retry with simplified queries if initial attempts failed
        primary_query = search_queries[0] if search_queries else query
        simplified_queries = simplify_query(primary_query)

        for simplified in simplified_queries:
            print(f"  Retrying with simplified query: {simplified}")
            image_urls = self._search_tavily(simplified)
            for image_url in image_urls:
                # Check URL deduplication before downloading
                if is_image_url_used(image_url):
                    print(f"  Skipping duplicate URL: {image_url[:50]}...")
                    continue
                base64_data = download_and_encode_base64(
                    image_url,
                    max_width=max_width,
                    max_height=max_height
                )
                if base64_data:
                    mark_image_url_used(image_url)
                    self._cache[search_queries[0].lower()] = base64_data
                    return base64_data

        return None

    def _build_search_queries(
        self,
        query: str,
        destination: str = "",
        category: str = ""
    ) -> list:
        """
        Build multiple search query variants for better image discovery.

        Returns a list of queries to try in order of specificity.
        """
        queries = []
        query_clean = query.strip()

        # Detect category from query if not provided
        if not category:
            query_lower = query.lower()
            if any(word in query_lower for word in ['ramen', 'sushi', 'restaurant', 'cafe', 'izakaya', 'food', 'dining']):
                category = "restaurant"
            elif any(word in query_lower for word in ['hotel', 'inn', 'hostel', 'resort', 'lodge']):
                category = "hotel"
            elif any(word in query_lower for word in ['temple', 'shrine', 'museum', 'park', 'tower', 'palace', 'castle']):
                category = "attraction"

        # Build queries based on category
        if category == "restaurant":
            # For restaurants, search for food/dishes rather than exterior
            queries.append(f"{query_clean} food dish")
            queries.append(f"{query_clean} menu signature dish")
            if destination:
                queries.append(f"{query_clean} {destination} restaurant interior")
            queries.append(f"{query_clean} cuisine")
        elif category == "hotel":
            # For hotels, search for exterior/lobby
            queries.append(f"{query_clean} hotel exterior building")
            if destination:
                queries.append(f"{query_clean} {destination} hotel")
            queries.append(f"{query_clean} lobby reception")
        elif category == "attraction":
            # For attractions, search with landmark keywords
            queries.append(f"{query_clean} landmark")
            if destination:
                queries.append(f"{query_clean} {destination}")
            queries.append(f"{query_clean} tourist photo")
        else:
            # Default: try with destination and photo keyword
            if destination and destination.lower() not in query.lower():
                queries.append(f"{query_clean} {destination}")
            queries.append(f"{query_clean} photo")
            queries.append(query_clean)

        return queries

    def search_multiple(
        self,
        queries: List[Dict[str, str]],
        destination: str = "",
        max_concurrent: int = 5
    ) -> Dict[str, str]:
        """
        Search for multiple images in parallel.

        Args:
            queries: List of dicts with 'key', 'query', and optional 'category' fields
                e.g., [{"key": "sensoji_temple", "query": "Sensoji Temple", "category": "attraction"}]
            destination: Destination context for all queries
            max_concurrent: Maximum concurrent searches

        Returns:
            Dictionary mapping keys to base64 data URIs
        """
        results = {}

        def search_single(item: Dict[str, str]) -> tuple:
            key = item.get("key", "")
            query = item.get("query", "")
            category = item.get("category", "")
            if not key or not query:
                return (key, None)

            result = self.search_image(query, destination, category=category)
            return (key, result)

        # Execute searches in parallel
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            futures = {executor.submit(search_single, q): q for q in queries}
            for future in as_completed(futures):
                try:
                    key, base64_data = future.result()
                    if key and base64_data:
                        results[key] = base64_data
                except Exception as e:
                    print(f"  Image search error: {str(e)}")

        return results

    def _search_tavily(self, query: str) -> List[str]:
        """Search for image URLs using Tavily API with enhanced query handling.

        Returns a list of image URLs (not just the first one) for deduplication.
        """
        try:
            from tavily import TavilyClient

            api_key = self.config.search.tavily_api_key
            if not api_key:
                return []

            client = TavilyClient(api_key=api_key)

            # Use include_images with advanced search for better quality and diversity
            response = client.search(
                query=query,
                max_results=5,
                search_depth="advanced",
                include_images=True
            )

            # Collect all valid image URLs
            valid_urls = []
            blocked_domains = ['placeholder', 'icon', 'logo', 'avatar', 'profile']

            # Get images from response
            images = response.get("images", [])
            for img in images:
                img_url = img if isinstance(img, str) else img.get("url", "")
                if img_url and not any(blocked in img_url.lower() for blocked in blocked_domains):
                    valid_urls.append(img_url)

            # Also add any blocked ones as fallback (at the end)
            for img in images:
                img_url = img if isinstance(img, str) else img.get("url", "")
                if img_url and img_url not in valid_urls:
                    valid_urls.append(img_url)

            # Fallback: try to extract image from result content
            results = response.get("results", [])
            for result in results:
                url = result.get("url", "")
                # Look for image-like URLs in the result URL
                if any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                    if url not in valid_urls:
                        valid_urls.append(url)

                # Check if content mentions images (some results have image URLs in content)
                content = result.get("content", "")
                if "https://" in content and any(ext in content.lower() for ext in ['.jpg', '.jpeg', '.png']):
                    # Extract image URLs from content
                    import re
                    img_matches = re.findall(r'(https?://[^\s<>"]+\.(?:jpg|jpeg|png|webp))', content, re.IGNORECASE)
                    for img_url in img_matches:
                        if img_url not in valid_urls:
                            valid_urls.append(img_url)

            return valid_urls

        except Exception as e:
            print(f"  Tavily image search error: {str(e)}")
            return []

    def search_hero_image(self, destination: str) -> Optional[str]:
        """
        Search for a high-quality hero image of a destination.

        Args:
            destination: Destination name (e.g., "Tokyo", "Paris")

        Returns:
            Base64 data URI or None
        """
        queries = [
            f"{destination} skyline panorama",
            f"{destination} city landmark",
            f"{destination} famous view"
        ]

        for query in queries:
            result = self.search_image(query, max_width=800, max_height=500)
            if result:
                return result

        return None
