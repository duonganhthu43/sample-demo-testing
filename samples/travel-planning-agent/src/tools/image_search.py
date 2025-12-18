"""
Image Search Tool for Travel Planning Agent
Searches for specific images based on query and returns base64 encoded data
"""

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional

from .image_utils import download_and_encode_base64, ImageCache


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
        max_height: int = 400
    ) -> Optional[str]:
        """
        Search for a specific image and return as base64.

        Args:
            query: Image search query (e.g., "Sensoji Temple")
            destination: Optional destination context (e.g., "Tokyo")
            max_width: Maximum image width
            max_height: Maximum image height

        Returns:
            Base64 data URI or None if not found
        """
        # Build search query with destination context
        if destination and destination.lower() not in query.lower():
            search_query = f"{query} {destination} photo"
        else:
            search_query = f"{query} photo"

        # Check cache first
        cache_key = search_query.lower()
        if cache_key in self._cache:
            return self._cache[cache_key]

        # Try Tavily image search
        image_url = self._search_tavily(search_query)
        if image_url:
            base64_data = download_and_encode_base64(
                image_url,
                max_width=max_width,
                max_height=max_height
            )
            if base64_data:
                self._cache[cache_key] = base64_data
                return base64_data

        return None

    def search_multiple(
        self,
        queries: List[Dict[str, str]],
        destination: str = "",
        max_concurrent: int = 5
    ) -> Dict[str, str]:
        """
        Search for multiple images in parallel.

        Args:
            queries: List of dicts with 'key' and 'query' fields
                e.g., [{"key": "sensoji_temple", "query": "Sensoji Temple"}]
            destination: Destination context for all queries
            max_concurrent: Maximum concurrent searches

        Returns:
            Dictionary mapping keys to base64 data URIs
        """
        results = {}

        def search_single(item: Dict[str, str]) -> tuple:
            key = item.get("key", "")
            query = item.get("query", "")
            if not key or not query:
                return (key, None)

            result = self.search_image(query, destination)
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

    def _search_tavily(self, query: str) -> Optional[str]:
        """Search for image URL using Tavily API"""
        try:
            from tavily import TavilyClient

            api_key = self.config.search.tavily_api_key
            if not api_key:
                return None

            client = TavilyClient(api_key=api_key)

            # Use include_images to get image results
            response = client.search(
                query=query,
                max_results=3,
                search_depth="basic",
                include_images=True
            )

            # Get images from response
            images = response.get("images", [])
            if images:
                # Return first image URL
                return images[0] if isinstance(images[0], str) else images[0].get("url")

            # Fallback: try to extract image from result content
            results = response.get("results", [])
            for result in results:
                url = result.get("url", "")
                # Look for image-like URLs
                if any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                    return url

            return None

        except Exception as e:
            print(f"  Tavily image search error: {str(e)}")
            return None

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
