"""
Hotel Search Tool
Searches for accommodations using Tavily API for real data
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re

from ..utils.config import get_config
from .image_utils import download_and_encode_base64, create_placeholder_svg


@dataclass
class HotelOption:
    """Hotel option data structure"""
    name: str
    location: str
    rating: float
    price_per_night: float
    amenities: List[str]
    distance_to_center: str
    near_transport: bool
    booking_url: str = ""
    description: str = ""
    image_url: Optional[str] = None
    image_base64: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "location": self.location,
            "rating": self.rating,
            "price_per_night": self.price_per_night,
            "amenities": self.amenities,
            "distance_to_center": self.distance_to_center,
            "near_transport": self.near_transport,
            "booking_url": self.booking_url,
            "description": self.description,
            "image_url": self.image_url,
            "image_base64": self.image_base64
        }


class HotelSearchTool:
    """
    Hotel search tool using Tavily API for real data
    """

    # In-memory cache
    _cache: Dict[tuple, List[HotelOption]] = {}

    # Common hotel chains for parsing
    HOTEL_CHAINS = [
        "Hilton", "Marriott", "Hyatt", "InterContinental", "Sheraton", "Westin",
        "Four Seasons", "Ritz-Carlton", "W Hotel", "Park Hyatt", "Grand Hyatt",
        "JW Marriott", "Conrad", "Mandarin Oriental", "Peninsula", "Shangri-La",
        "Sofitel", "Novotel", "Ibis", "Holiday Inn", "Crowne Plaza", "Radisson",
        "Best Western", "Hampton Inn", "DoubleTree", "Embassy Suites",
        "APA Hotel", "Dormy Inn", "Tokyu Stay", "Mitsui Garden", "Prince Hotel"
    ]

    # Standard amenities
    COMMON_AMENITIES = [
        "Free WiFi", "Air Conditioning", "Restaurant", "Fitness Center",
        "Business Center", "Concierge", "Room Service", "Laundry Service"
    ]

    def __init__(self):
        self.config = get_config()
        self.mock_mode = self.config.app.mock_external_apis

        if not self.config.search.tavily_api_key:
            if self.mock_mode:
                print("Tavily key not found - using mock mode for hotels")
            else:
                raise ValueError("TAVILY_API_KEY is required when MOCK_EXTERNAL_APIS=false")
        print(f"HotelSearchTool initialized with Tavily (mock_mode: {self.mock_mode})")

    def search_hotels(
        self,
        destination: str,
        check_in: str,
        check_out: str,
        max_budget_per_night: Optional[float] = None,
        prefer_near_transport: bool = True,
        min_rating: float = 3.5
    ) -> Dict[str, Any]:
        """
        Search for hotels using Tavily

        Args:
            destination: City/location to search
            check_in: Check-in date
            check_out: Check-out date
            max_budget_per_night: Maximum price per night
            prefer_near_transport: Prefer hotels near public transport
            min_rating: Minimum rating filter

        Returns:
            Dictionary with hotel options
        """
        cache_key = (destination.lower(), check_in, check_out)

        if cache_key in HotelSearchTool._cache:
            print(f"Cache hit for hotels in {destination}")
            return self._format_cached_result(
                cache_key, max_budget_per_night, prefer_near_transport, min_rating
            )

        print(f"Searching hotels in {destination} ({check_in} to {check_out}) via Tavily...")

        if self.mock_mode:
            hotels = self._generate_fallback_hotels(destination)
        else:
            hotels = self._search_tavily_hotels(destination)

        HotelSearchTool._cache[cache_key] = hotels

        return self._format_result(
            hotels, max_budget_per_night, prefer_near_transport, min_rating
        )

    def _search_tavily_hotels(self, destination: str) -> List[HotelOption]:
        """Search for hotels using Tavily API"""
        try:
            from tavily import TavilyClient

            client = TavilyClient(api_key=self.config.search.tavily_api_key)
            hotels = []
            seen_hotels = set()
            collected_images = []  # Collect images from all queries

            # Build search queries
            queries = [
                f"best hotels in {destination} reviews prices",
                f"{destination} hotel recommendations where to stay",
                f"top rated hotels {destination} near station",
                f"{destination} budget hotels hostels accommodation",
            ]

            for query in queries[:4]:
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
                        parsed_hotels = self._parse_tavily_hotel_result(result, destination)
                        for hotel in parsed_hotels:
                            if hotel.name not in seen_hotels:
                                seen_hotels.add(hotel.name)
                                hotels.append(hotel)

                except Exception as e:
                    print(f"  Query failed: {str(e)}")
                    continue

            # Assign images to hotels
            self._assign_images_to_hotels(hotels, collected_images)

            print(f"Found {len(hotels)} hotel options via Tavily (with {len(collected_images)} images)")

            return hotels

        except Exception as e:
            print(f"Tavily hotel search failed: {str(e)}")
            if self.mock_mode:
                return self._generate_fallback_hotels(destination)
            raise

    def _assign_images_to_hotels(
        self,
        hotels: List[HotelOption],
        image_urls: List[str]
    ) -> None:
        """Assign and encode images to hotels"""
        if not image_urls:
            if self.mock_mode:
                for hotel in hotels:
                    hotel.image_base64 = create_placeholder_svg(hotel.name)
            return

        # Distribute images to hotels (round-robin if fewer images than hotels)
        for i, hotel in enumerate(hotels):
            if i < len(image_urls):
                image_url = image_urls[i]
                hotel.image_url = image_url
                print(f"  Downloading image for {hotel.name}...")
                hotel.image_base64 = download_and_encode_base64(image_url)

                # Use placeholder if download failed
                if not hotel.image_base64:
                    if self.mock_mode:
                        hotel.image_base64 = create_placeholder_svg(hotel.name)
            else:
                # No more images, use placeholder
                if self.mock_mode:
                    hotel.image_base64 = create_placeholder_svg(hotel.name)

    def _parse_tavily_hotel_result(
        self,
        result: Dict[str, Any],
        destination: str
    ) -> List[HotelOption]:
        """Parse a Tavily search result into HotelOptions"""
        hotels = []
        title = result.get("title", "")
        content = result.get("content", "")
        url = result.get("url", "")

        if not content:
            return hotels

        # Try to find hotel names in content
        hotels_found = []

        # Look for known hotel chains
        for chain in self.HOTEL_CHAINS:
            if chain.lower() in content.lower():
                # Try to extract full hotel name
                pattern = rf'{chain}[^,.\n]*?(?:Hotel|Inn|Suites|Resort)?'
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    hotels_found.append(matches[0].strip())
                else:
                    hotels_found.append(f"{chain} {destination}")

        # Extract prices
        prices = re.findall(r'\$(\d{2,4})', content)

        # Extract ratings
        rating_match = re.search(r'(\d+\.?\d*)\s*(?:out of\s*5|/5|stars?|rating)', content.lower())
        base_rating = float(rating_match.group(1)) if rating_match and float(rating_match.group(1)) <= 5 else 4.2

        # Check for amenities mentioned
        amenities_found = []
        amenity_keywords = {
            "wifi": "Free WiFi",
            "pool": "Pool",
            "gym": "Fitness Center",
            "fitness": "Fitness Center",
            "restaurant": "Restaurant",
            "spa": "Spa",
            "breakfast": "Breakfast Included",
            "parking": "Parking",
            "business": "Business Center"
        }
        for keyword, amenity in amenity_keywords.items():
            if keyword in content.lower():
                amenities_found.append(amenity)

        if not amenities_found:
            amenities_found = self.COMMON_AMENITIES[:4]

        # Check for location/transport mentions
        near_transport = any(word in content.lower() for word in ['station', 'metro', 'subway', 'train', 'convenient', 'central'])

        # Create hotel options
        for i, hotel_name in enumerate(hotels_found[:3]):
            price = float(prices[min(i, len(prices)-1)]) if prices else self._estimate_price(hotel_name)
            rating = base_rating + (0.1 * (2 - i))  # Slight variation

            hotels.append(HotelOption(
                name=hotel_name,
                location=f"{destination}",
                rating=min(5.0, rating),
                price_per_night=price,
                amenities=amenities_found,
                distance_to_center="0.5-2 km",
                near_transport=near_transport,
                booking_url=url,
                description=content[:200] + "..." if len(content) > 200 else content
            ))

        return hotels

    def _estimate_price(self, hotel_name: str) -> float:
        """Estimate price based on hotel name"""
        luxury_keywords = ["ritz", "four seasons", "mandarin", "peninsula", "park hyatt", "w hotel"]
        mid_keywords = ["hilton", "marriott", "hyatt", "sheraton", "westin", "sofitel"]
        budget_keywords = ["ibis", "holiday inn", "best western", "apa", "dormy"]

        name_lower = hotel_name.lower()

        if any(kw in name_lower for kw in luxury_keywords):
            return 400
        elif any(kw in name_lower for kw in mid_keywords):
            return 180
        elif any(kw in name_lower for kw in budget_keywords):
            return 80
        else:
            return 120

    def _generate_fallback_hotels(self, destination: str) -> List[HotelOption]:
        """Generate fallback hotel options with placeholder images"""
        import random

        hotels = [
            (f"Grand Hotel {destination}", 4.5, 200, True),
            (f"Central Inn {destination}", 4.0, 100, True),
            (f"{destination} Plaza Hotel", 4.3, 150, True),
            (f"Budget Stay {destination}", 3.7, 60, False),
            (f"Luxury Suites {destination}", 4.8, 350, True),
        ]

        result = []
        for name, rating, base_price, near in hotels:
            amenities = random.sample(self.COMMON_AMENITIES, min(5, len(self.COMMON_AMENITIES)))
            result.append(HotelOption(
                name=name,
                location=destination,
                rating=rating,
                price_per_night=base_price + random.uniform(-20, 30),
                amenities=amenities,
                distance_to_center=f"{random.uniform(0.3, 2.5):.1f} km",
                near_transport=near,
                booking_url="",
                description=f"Comfortable accommodation in {destination} with modern amenities.",
                image_base64=create_placeholder_svg(name)
            ))

        return result

    def _format_result(
        self,
        hotels: List[HotelOption],
        max_budget: Optional[float],
        prefer_near_transport: bool,
        min_rating: float
    ) -> Dict[str, Any]:
        """Format search results"""
        filtered = hotels.copy()

        # Apply filters
        if max_budget:
            filtered = [h for h in filtered if h.price_per_night <= max_budget]

        filtered = [h for h in filtered if h.rating >= min_rating]

        # Sort by preference
        if prefer_near_transport:
            filtered.sort(key=lambda x: (not x.near_transport, -x.rating, x.price_per_night))
        else:
            filtered.sort(key=lambda x: (-x.rating, x.price_per_night))

        # Find recommendations
        best_value = min(filtered, key=lambda x: x.price_per_night / x.rating) if filtered else None
        highest_rated = max(filtered, key=lambda x: x.rating) if filtered else None

        return {
            "hotels": [h.to_dict() for h in filtered[:8]],
            "best_value": best_value.to_dict() if best_value else None,
            "highest_rated": highest_rated.to_dict() if highest_rated else None,
            "total_options": len(filtered),
            "filters_applied": {
                "max_budget": max_budget,
                "min_rating": min_rating,
                "near_transport": prefer_near_transport
            }
        }

    def _format_cached_result(
        self,
        cache_key: tuple,
        max_budget: Optional[float],
        prefer_near_transport: bool,
        min_rating: float
    ) -> Dict[str, Any]:
        """Format cached results"""
        cached = HotelSearchTool._cache[cache_key]
        return self._format_result(cached, max_budget, prefer_near_transport, min_rating)
