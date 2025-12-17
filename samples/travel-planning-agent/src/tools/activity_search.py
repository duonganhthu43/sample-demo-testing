"""
Activity Search Tool
Searches for attractions and activities using Tavily API
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
import re

from ..utils.config import get_config
from .image_utils import download_and_encode_base64, create_placeholder_svg


@dataclass
class ActivityOption:
    """Activity/attraction data structure"""
    name: str
    category: str
    description: str
    location: str
    duration: str
    price: float
    rating: float
    best_time: str
    tips: List[str]
    source_url: Optional[str] = None
    image_url: Optional[str] = None
    image_base64: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "location": self.location,
            "duration": self.duration,
            "price": self.price,
            "rating": self.rating,
            "best_time": self.best_time,
            "tips": self.tips,
            "source_url": self.source_url,
            "image_url": self.image_url,
            "image_base64": self.image_base64
        }


class ActivitySearchTool:
    """
    Activity/attraction search tool using Tavily API
    """

    # In-memory cache
    _cache: Dict[tuple, List[ActivityOption]] = {}

    # Category keywords for classification
    CATEGORY_KEYWORDS = {
        "Cultural": ["temple", "shrine", "museum", "palace", "castle", "historical", "heritage", "traditional"],
        "Food": ["food", "restaurant", "cuisine", "eat", "dining", "market", "street food", "culinary", "ramen", "sushi"],
        "Nature": ["park", "garden", "mountain", "beach", "lake", "nature", "hiking", "scenic", "forest"],
        "Sightseeing": ["tower", "view", "landmark", "district", "neighborhood", "walking", "tour", "crossing"],
        "Shopping": ["shopping", "mall", "market", "district", "electronics", "fashion", "souvenir"],
        "Entertainment": ["show", "theme park", "entertainment", "nightlife", "bar", "club", "karaoke"],
        "Museum": ["museum", "gallery", "art", "exhibition", "science"],
        "Adventure": ["adventure", "outdoor", "sports", "cycling", "diving", "surfing"]
    }

    def __init__(self):
        self.config = get_config()
        self.mock_mode = self.config.app.mock_external_apis

        # Auto-enable mock mode if Tavily API key is missing
        if not self.config.search.tavily_api_key:
            self.mock_mode = True
            print("Tavily key not found - using mock mode for activities")
        else:
            print(f"ActivitySearchTool initialized with Tavily (mock_mode: {self.mock_mode})")

    def search_activities(
        self,
        destination: str,
        interests: Optional[List[str]] = None,
        max_budget_per_activity: Optional[float] = None,
        include_free: bool = True
    ) -> Dict[str, Any]:
        """
        Search for activities and attractions using Tavily

        Args:
            destination: City/location
            interests: List of interest categories (e.g., ["Cultural", "Food"])
            max_budget_per_activity: Maximum price per activity
            include_free: Include free activities

        Returns:
            Dictionary with activity options
        """
        cache_key = (destination.lower(), tuple(interests or []))

        if cache_key in ActivitySearchTool._cache:
            print(f"Cache hit for activities in {destination}")
            return self._format_cached_result(
                cache_key, max_budget_per_activity, include_free
            )

        print(f"Searching activities in {destination} via Tavily...")

        if self.mock_mode:
            activities = self._generate_fallback_activities(destination)
        else:
            activities = self._search_tavily_activities(destination, interests)

        ActivitySearchTool._cache[cache_key] = activities

        return self._format_result(
            activities, interests, max_budget_per_activity, include_free
        )

    def _search_tavily_activities(
        self,
        destination: str,
        interests: Optional[List[str]] = None
    ) -> List[ActivityOption]:
        """Search for activities using Tavily API"""
        try:
            from tavily import TavilyClient

            client = TavilyClient(api_key=self.config.search.tavily_api_key)
            activities = []
            seen_names = set()
            collected_images = []  # Collect images from all queries

            # Build search queries
            queries = [
                f"best things to do in {destination} top attractions 2024",
                f"{destination} must visit places tourist attractions",
                f"{destination} travel guide popular activities",
            ]

            # Add interest-specific queries
            if interests:
                for interest in interests[:2]:
                    queries.append(f"{destination} best {interest.lower()} activities places")
            else:
                queries.extend([
                    f"{destination} cultural attractions temples museums",
                    f"{destination} best food restaurants local cuisine",
                ])

            for query in queries[:5]:
                try:
                    print(f"  Tavily query: {query}")
                    response = client.search(
                        query=query,
                        max_results=5,
                        search_depth="basic",
                        include_images=True  # Enable image fetching
                    )

                    # Collect images from the response
                    images = response.get("images", [])
                    for img in images:
                        if isinstance(img, str):
                            collected_images.append(img)
                        elif isinstance(img, dict) and img.get("url"):
                            collected_images.append(img["url"])

                    for result in response.get("results", []):
                        activity = self._parse_tavily_result(result, destination)
                        if activity and activity.name not in seen_names:
                            seen_names.add(activity.name)
                            activities.append(activity)

                except Exception as e:
                    print(f"  Query failed: {str(e)}")
                    continue

            # Assign images to activities
            self._assign_images_to_activities(activities, collected_images)

            print(f"Found {len(activities)} activities via Tavily (with {len(collected_images)} images)")
            return activities if activities else self._generate_fallback_activities(destination)

        except Exception as e:
            print(f"Tavily activity search failed: {str(e)}")
            return self._generate_fallback_activities(destination)

    def _assign_images_to_activities(
        self,
        activities: List[ActivityOption],
        image_urls: List[str]
    ) -> None:
        """Assign and encode images to activities"""
        if not image_urls:
            # Use placeholders if no images available
            for activity in activities:
                activity.image_base64 = create_placeholder_svg(activity.name)
            return

        # Distribute images to activities (round-robin if fewer images than activities)
        for i, activity in enumerate(activities):
            if i < len(image_urls):
                image_url = image_urls[i]
                activity.image_url = image_url
                print(f"  Downloading image for {activity.name}...")
                activity.image_base64 = download_and_encode_base64(image_url)

                # Use placeholder if download failed
                if not activity.image_base64:
                    activity.image_base64 = create_placeholder_svg(activity.name)
            else:
                # No more images, use placeholder
                activity.image_base64 = create_placeholder_svg(activity.name)

    def _parse_tavily_result(
        self,
        result: Dict[str, Any],
        destination: str
    ) -> Optional[ActivityOption]:
        """Parse a Tavily search result into an ActivityOption"""
        title = result.get("title", "")
        content = result.get("content", "")
        url = result.get("url", "")

        if not title or not content:
            return None

        # Extract activity name from title
        name = self._extract_activity_name(title)
        if not name or len(name) < 5:
            return None

        # Classify category
        category = self._classify_category(title + " " + content)

        # Extract or estimate other fields
        description = content[:350] + "..." if len(content) > 350 else content
        duration = self._estimate_duration(category)
        price = self._estimate_price(content, category)
        rating = self._estimate_rating(content)
        best_time = self._suggest_best_time(category)
        tips = self._extract_tips(content)

        return ActivityOption(
            name=name,
            category=category,
            description=description,
            location=destination,
            duration=duration,
            price=price,
            rating=rating,
            best_time=best_time,
            tips=tips,
            source_url=url
        )

    def _extract_activity_name(self, title: str) -> str:
        """Extract a clean activity name from title"""
        name = title

        # Remove common patterns
        patterns_to_remove = [
            r'\s*-\s*[^-]{20,}$',  # Long suffix after dash
            r'\s*\|.*$',
            r'\(\d{4}\)',
            r'^\d+\.\s*',
            r'^best\s+',
            r'^top\s+\d+\s+',
        ]

        for pattern in patterns_to_remove:
            name = re.sub(pattern, '', name, flags=re.IGNORECASE)

        name = name.strip()

        # Skip generic titles
        generic = ['things to do', 'travel guide', 'tourism', 'tripadvisor', 'booking.com']
        if any(g in name.lower() for g in generic) and len(name) < 40:
            return ""

        return name[:80]

    def _classify_category(self, text: str) -> str:
        """Classify activity category based on text content"""
        text_lower = text.lower()

        category_scores = {}
        for category, keywords in self.CATEGORY_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw in text_lower)
            if score > 0:
                category_scores[category] = score

        if category_scores:
            return max(category_scores, key=category_scores.get)

        return "Sightseeing"

    def _estimate_duration(self, category: str) -> str:
        """Estimate activity duration based on category"""
        durations = {
            "Cultural": "2-3 hours",
            "Food": "2-3 hours",
            "Nature": "3-4 hours",
            "Sightseeing": "1-2 hours",
            "Shopping": "2-4 hours",
            "Entertainment": "2-3 hours",
            "Museum": "2-3 hours",
            "Adventure": "4-6 hours"
        }
        return durations.get(category, "2-3 hours")

    def _estimate_price(self, content: str, category: str) -> float:
        """Estimate activity price"""
        content_lower = content.lower()

        if any(word in content_lower for word in ['free entry', 'free admission', 'no fee', 'free to visit', 'no charge']):
            return 0

        price_match = re.search(r'\$(\d+)', content)
        if price_match:
            return float(price_match.group(1))

        default_prices = {
            "Cultural": 10,
            "Food": 30,
            "Nature": 5,
            "Sightseeing": 15,
            "Shopping": 0,
            "Entertainment": 50,
            "Museum": 20,
            "Adventure": 75
        }
        return default_prices.get(category, 20)

    def _estimate_rating(self, content: str) -> float:
        """Estimate rating from content"""
        rating_match = re.search(r'(\d+\.?\d*)\s*(?:out of\s*5|/5|stars?)', content.lower())
        if rating_match:
            rating = float(rating_match.group(1))
            if rating <= 5:
                return rating

        positive_words = ['must-see', 'must see', 'top rated', 'highly recommended', 'popular', 'famous', 'iconic', 'best']
        if any(word in content.lower() for word in positive_words):
            return 4.5

        return 4.2

    def _suggest_best_time(self, category: str) -> str:
        """Suggest best time to visit based on category"""
        best_times = {
            "Cultural": "Early morning to avoid crowds",
            "Food": "Lunch (11am-2pm) or dinner (6-8pm)",
            "Nature": "Morning for best weather and photos",
            "Sightseeing": "Weekday mornings or sunset",
            "Shopping": "Afternoon on weekdays",
            "Entertainment": "Evening shows",
            "Museum": "Weekday mornings",
            "Adventure": "Morning with good weather"
        }
        return best_times.get(category, "Morning or late afternoon")

    def _extract_tips(self, content: str) -> List[str]:
        """Extract tips from content"""
        tips = []

        tip_patterns = [
            r'tip[s]?:?\s*([^.!?]{10,60}[.!?])',
            r'recommend[s]?\s+([^.!?]{10,60}[.!?])',
            r'don\'t miss\s+([^.!?]{10,60}[.!?])',
        ]

        for pattern in tip_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            tips.extend(matches[:1])

        if not tips:
            tips = ["Check opening hours before visiting", "Book online to skip queues"]

        return tips[:3]

    def _generate_fallback_activities(self, destination: str) -> List[ActivityOption]:
        """Generate fallback activity options with placeholder images"""
        activities = [
            ActivityOption(
                name=f"{destination} City Walking Tour",
                category="Sightseeing",
                description=f"Explore the highlights of {destination} with a guided walking tour",
                location=destination,
                duration="3 hours",
                price=25,
                rating=4.3,
                best_time="Morning",
                tips=["Wear comfortable shoes", "Bring water"],
                source_url=None,
                image_base64=create_placeholder_svg(f"{destination} Walking Tour")
            ),
            ActivityOption(
                name=f"{destination} Food Tour",
                category="Food",
                description=f"Taste local cuisine and discover hidden food gems in {destination}",
                location=destination,
                duration="3-4 hours",
                price=50,
                rating=4.6,
                best_time="Lunch time",
                tips=["Come hungry", "Inform of dietary restrictions"],
                source_url=None,
                image_base64=create_placeholder_svg(f"{destination} Food Tour")
            ),
            ActivityOption(
                name=f"{destination} Cultural Experience",
                category="Cultural",
                description=f"Immerse yourself in the local culture and traditions of {destination}",
                location=destination,
                duration="2-3 hours",
                price=30,
                rating=4.4,
                best_time="Morning or afternoon",
                tips=["Book in advance", "Dress respectfully"],
                source_url=None,
                image_base64=create_placeholder_svg(f"{destination} Cultural")
            ),
        ]
        return activities

    def _format_result(
        self,
        activities: List[ActivityOption],
        interests: Optional[List[str]],
        max_budget: Optional[float],
        include_free: bool
    ) -> Dict[str, Any]:
        """Format search results"""
        filtered = activities.copy()

        if interests:
            interests_lower = [i.lower() for i in interests]
            filtered = [a for a in filtered if a.category.lower() in interests_lower]
            if not filtered:
                filtered = activities.copy()

        if max_budget is not None:
            if include_free:
                filtered = [a for a in filtered if a.price <= max_budget]
            else:
                filtered = [a for a in filtered if 0 < a.price <= max_budget]

        filtered.sort(key=lambda x: -x.rating)

        by_category = {}
        for act in filtered:
            if act.category not in by_category:
                by_category[act.category] = []
            by_category[act.category].append(act.to_dict())

        must_do = [a.to_dict() for a in filtered if a.rating >= 4.5][:3]
        free_activities = [a.to_dict() for a in filtered if a.price == 0]

        return {
            "activities": [a.to_dict() for a in filtered],
            "by_category": by_category,
            "must_do": must_do,
            "free_activities": free_activities,
            "total_options": len(filtered)
        }

    def _format_cached_result(
        self,
        cache_key: tuple,
        max_budget: Optional[float],
        include_free: bool
    ) -> Dict[str, Any]:
        """Format cached results"""
        cached = ActivitySearchTool._cache[cache_key]
        interests = list(cache_key[1]) if cache_key[1] else None
        return self._format_result(cached, interests, max_budget, include_free)
