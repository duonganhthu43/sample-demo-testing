"""
Image Agent for Travel Planning
Fetches specific images based on itinerary content for better visual presentation
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set
import re

from ..utils.config import get_config
from ..tools.image_search import ImageSearchTool
from ..tools.image_utils import normalize_image_key


@dataclass
class ImageFetchResult:
    """Result from image fetching operation"""
    images: Dict[str, str]  # key -> base64 data URI
    total_requested: int
    total_fetched: int
    failed_keys: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "images": self.images,
            "total_requested": self.total_requested,
            "total_fetched": self.total_fetched,
            "failed_keys": self.failed_keys
        }


class ImageAgent:
    """
    Agent for fetching specific images based on itinerary content.

    Instead of pre-downloading generic images during research,
    this agent analyzes the generated itinerary and fetches
    targeted images for each activity, attraction, and hotel.
    """

    def __init__(self, config=None):
        self.config = config or get_config()
        self.image_search = ImageSearchTool(config)

    def fetch_images_for_itinerary(
        self,
        itinerary: Dict[str, Any],
        context: Dict[str, Any],
        max_images: int = 15
    ) -> ImageFetchResult:
        """
        Fetch specific images based on itinerary content.

        Args:
            itinerary: Generated itinerary data with days/schedule
            context: Context containing destination info, research results
            max_images: Maximum number of images to fetch

        Returns:
            ImageFetchResult with fetched images
        """
        print("ImageAgent: Analyzing itinerary for image requirements...")

        # Extract destination
        destination = self._extract_destination(itinerary, context)

        # Build list of image queries from itinerary
        image_queries = self._extract_image_queries(itinerary, context, destination)

        # Limit and prioritize
        prioritized = self._prioritize_queries(image_queries, max_images)

        print(f"  Found {len(image_queries)} potential images, fetching top {len(prioritized)}")

        # Fetch images
        results = {}
        failed = []

        # Always try to get hero image first
        hero = self.image_search.search_hero_image(destination)
        if hero:
            results["hero"] = hero
            print(f"  Fetched hero image for {destination}")

        # Fetch remaining images
        if prioritized:
            fetched = self.image_search.search_multiple(
                prioritized,
                destination=destination,
                max_concurrent=5
            )
            results.update(fetched)

            # Track failures
            for query in prioritized:
                key = query.get("key", "")
                if key and key not in results:
                    failed.append(key)

        print(f"  Fetched {len(results)} images ({len(failed)} failed)")

        return ImageFetchResult(
            images=results,
            total_requested=len(prioritized) + 1,  # +1 for hero
            total_fetched=len(results),
            failed_keys=failed
        )

    def _extract_destination(
        self,
        itinerary: Dict[str, Any],
        context: Dict[str, Any]
    ) -> str:
        """Extract destination name from itinerary or context"""
        # Try itinerary first
        dest = itinerary.get("destination", "")
        if dest:
            return dest

        # Try context
        for item in context.get("research", []):
            if isinstance(item, dict) and item.get("type") == "destination":
                return item.get("destination", "")

        return ""

    def _extract_image_queries(
        self,
        itinerary: Dict[str, Any],
        context: Dict[str, Any],
        destination: str
    ) -> List[Dict[str, str]]:
        """
        Extract image queries from itinerary content.

        Looks for:
        - image_suggestion fields in schedule items
        - Activity names that are landmarks/attractions
        - Hotel names
        """
        queries = []
        seen_keys: Set[str] = set()
        # Extract from daily schedule
        for day in itinerary.get("days", []):
            for item in day.get("schedule", []):
                # Check for explicit image_suggestion
                suggestion = item.get("image_suggestion", "")
                if suggestion and suggestion not in seen_keys:
                    seen_keys.add(suggestion)
                    # Convert suggestion key to human-readable query
                    query = self._suggestion_to_query(suggestion, destination)
                    # Detect category for better image search
                    item_category = item.get("category", "").lower()
                    search_category = self._map_category(item_category, suggestion)
                    # Normalize the key for consistent matching
                    normalized_key = self._normalize_key(suggestion) or suggestion
                    queries.append({
                        "key": normalized_key,
                        "query": query,
                        "priority": self._get_priority(item),
                        "category": search_category
                    })

                # Also check activity name for landmarks
                activity = item.get("activity", "")
                item_category = item.get("category", "").lower()
                if activity and item_category in ["sightseeing", "cultural", "entertainment"]:
                    key = self._normalize_key(activity)
                    if key and key not in seen_keys:
                        seen_keys.add(key)
                        queries.append({
                            "key": key,
                            "query": activity,
                            "priority": 2,
                            "category": "attraction"
                        })

        # Extract hotel images from context
        for item in context.get("research", []):
            if isinstance(item, dict) and item.get("type") == "accommodations":
                # Get the recommended/selected hotel
                best_value = item.get("best_value", {})
                highest_rated = item.get("highest_rated", {})
                hotels = item.get("hotels", [])[:3]

                for hotel in [best_value, highest_rated] + hotels:
                    if isinstance(hotel, dict):
                        name = hotel.get("name", "")
                        if name:
                            key = self._normalize_key(name)
                            if key and not self._is_duplicate(key, seen_keys):
                                seen_keys.add(key)
                                queries.append({
                                    "key": key,
                                    "query": f"{name} hotel {destination}",
                                    "priority": 3,
                                    "category": "hotel"
                                })

        # Extract restaurant/food images from context
        for item in context.get("research", []):
            if isinstance(item, dict) and item.get("type") == "restaurants":
                # Get restaurants for images - include more to increase match chances
                all_restaurants = []
                all_restaurants.extend(item.get("dinner_options", [])[:5])
                all_restaurants.extend(item.get("lunch_options", [])[:5])
                all_restaurants.extend(item.get("breakfast_options", [])[:3])

                for restaurant in all_restaurants:
                    if isinstance(restaurant, dict):
                        name = restaurant.get("name", "")
                        image_suggestion = restaurant.get("image_suggestion", "")
                        cuisine = restaurant.get("cuisine_type", "food")
                        specialty = restaurant.get("specialty_dishes", [])

                        if name:
                            # Normalize both image_suggestion and name for consistent keys
                            key = self._normalize_key(image_suggestion) if image_suggestion else self._normalize_key(name)
                            if key and not self._is_duplicate(key, seen_keys):
                                seen_keys.add(key)
                                # Build specific query with restaurant name and specialty
                                if specialty:
                                    dish = specialty[0] if isinstance(specialty, list) else specialty
                                    query = f"{name} {dish}"
                                else:
                                    query = f"{name} {cuisine}"
                                queries.append({
                                    "key": key,
                                    "query": query,
                                    "priority": 4,  # Lower priority than attractions
                                    "category": "restaurant"
                                })

        return queries

    def _map_category(self, item_category: str, suggestion: str) -> str:
        """Map itinerary category to image search category"""
        suggestion_lower = suggestion.lower()

        # Check suggestion for food-related keywords
        food_keywords = ['ramen', 'sushi', 'restaurant', 'cafe', 'izakaya', 'dining', 'food', 'lunch', 'dinner', 'breakfast']
        if any(kw in suggestion_lower for kw in food_keywords):
            return "restaurant"

        # Check suggestion for hotel keywords
        hotel_keywords = ['hotel', 'inn', 'hostel', 'resort', 'lodge', 'ryokan']
        if any(kw in suggestion_lower for kw in hotel_keywords):
            return "hotel"

        # Map by item category
        if item_category in ["food", "meal", "dining"]:
            return "restaurant"
        elif item_category in ["sightseeing", "cultural", "entertainment", "shopping"]:
            return "attraction"
        elif item_category == "hotel":
            return "hotel"

        return "attraction"  # Default to attraction

    def _is_duplicate(self, key: str, seen_keys: Set[str]) -> bool:
        """
        Check if key is a duplicate, accounting for variations.
        e.g., 'sensoji_temple' and 'sensojitemple' should be considered duplicates.
        """
        if key in seen_keys:
            return True

        # Strip underscores for comparison
        stripped = key.replace('_', '').replace('-', '')
        for seen in seen_keys:
            seen_stripped = seen.replace('_', '').replace('-', '')
            if stripped == seen_stripped:
                return True
            # Also check if one contains the other
            if len(stripped) > 5 and len(seen_stripped) > 5:
                if stripped in seen_stripped or seen_stripped in stripped:
                    return True

        return False

    def _suggestion_to_query(self, suggestion: str, destination: str) -> str:
        """
        Convert image_suggestion key to human-readable search query.

        Examples:
            sensoji_temple -> Sensoji Temple Tokyo
            tokyo_tower -> Tokyo Tower
            shibuya_crossing -> Shibuya Crossing Tokyo
        """
        # Replace underscores with spaces and title case
        query = suggestion.replace("_", " ").title()

        # Add destination if not already in query
        if destination and destination.lower() not in query.lower():
            query = f"{query} {destination}"

        return query

    def _normalize_key(self, name: str) -> str:
        """Normalize a name to use as an image key"""
        return normalize_image_key(name)

    def _get_priority(self, schedule_item: Dict[str, Any]) -> int:
        """
        Get priority score for an image (lower = higher priority).

        Priority is based on:
        - Category (sightseeing > cultural > other)
        - Cost (free/cheap attractions often iconic)
        - Whether it has explicit image_suggestion
        """
        category = schedule_item.get("category", "").lower()
        has_suggestion = bool(schedule_item.get("image_suggestion"))

        if has_suggestion:
            return 1
        elif category in ["sightseeing", "cultural"]:
            return 2
        elif category in ["entertainment", "shopping"]:
            return 3
        else:
            return 4

    def _prioritize_queries(
        self,
        queries: List[Dict[str, str]],
        max_images: int
    ) -> List[Dict[str, str]]:
        """
        Prioritize and limit image queries.

        Returns top queries sorted by priority.
        """
        # Sort by priority (lower = higher priority)
        sorted_queries = sorted(queries, key=lambda x: x.get("priority", 99))

        # Deduplicate by key
        seen = set()
        unique = []
        for q in sorted_queries:
            key = q.get("key", "")
            if key and key not in seen:
                seen.add(key)
                unique.append(q)

        # Limit to max_images
        return unique[:max_images]
