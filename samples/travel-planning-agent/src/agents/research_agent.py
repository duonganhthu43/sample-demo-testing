"""
Research Agent for Travel Planning
Gathers information about destinations, flights, hotels, and activities using Tavily
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import re

from ..utils.config import get_config
from ..utils.prompts import RESEARCH_AGENT_PROMPT
from ..tools import FlightSearchTool, HotelSearchTool, ActivitySearchTool


@dataclass
class DestinationResult:
    """Result from destination research"""
    destination: str
    overview: str
    visa_requirements: str
    best_time_to_visit: str
    language: str
    currency: str
    time_zone: str
    cultural_tips: List[str]
    safety_rating: str
    local_cuisine: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "destination": self.destination,
            "overview": self.overview,
            "visa_requirements": self.visa_requirements,
            "best_time_to_visit": self.best_time_to_visit,
            "language": self.language,
            "currency": self.currency,
            "time_zone": self.time_zone,
            "cultural_tips": self.cultural_tips,
            "safety_rating": self.safety_rating,
            "local_cuisine": self.local_cuisine,
            "sources": self.sources
        }


@dataclass
class FlightResearchResult:
    """Result from flight research"""
    origin: str
    destination: str
    departure_date: str
    return_date: Optional[str]
    outbound_options: List[Dict[str, Any]]
    return_options: List[Dict[str, Any]]
    best_outbound: Optional[Dict[str, Any]]
    best_return: Optional[Dict[str, Any]]
    total_options: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "origin": self.origin,
            "destination": self.destination,
            "departure_date": self.departure_date,
            "return_date": self.return_date,
            "outbound_options": self.outbound_options,
            "return_options": self.return_options,
            "best_outbound": self.best_outbound,
            "best_return": self.best_return,
            "total_options": self.total_options
        }


@dataclass
class AccommodationResult:
    """Result from accommodation research"""
    destination: str
    check_in: str
    check_out: str
    hotels: List[Dict[str, Any]]
    best_value: Optional[Dict[str, Any]]
    highest_rated: Optional[Dict[str, Any]]
    total_options: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "destination": self.destination,
            "check_in": self.check_in,
            "check_out": self.check_out,
            "hotels": self.hotels,
            "best_value": self.best_value,
            "highest_rated": self.highest_rated,
            "total_options": self.total_options
        }


@dataclass
class ActivityResearchResult:
    """Result from activity research"""
    destination: str
    activities: List[Dict[str, Any]]
    by_category: Dict[str, List[Dict[str, Any]]]
    must_do: List[Dict[str, Any]]
    free_activities: List[Dict[str, Any]]
    total_options: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "destination": self.destination,
            "activities": self.activities,
            "by_category": self.by_category,
            "must_do": self.must_do,
            "free_activities": self.free_activities,
            "total_options": self.total_options
        }


class ResearchAgent:
    """
    Research agent for gathering travel information using Tavily
    """

    def __init__(self, config=None):
        self.config = config or get_config()
        self.flight_tool = FlightSearchTool()
        self.hotel_tool = HotelSearchTool()
        self.activity_tool = ActivitySearchTool()
        self.mock_mode = self.config.app.mock_external_apis

        if not self.config.search.tavily_api_key:
            self.mock_mode = True
            print("Tavily key not found - using fallback for destination research")
        else:
            print(f"ResearchAgent initialized with Tavily (mock_mode: {self.mock_mode})")

    def research_destination(self, destination: str) -> DestinationResult:
        """
        Research destination information using Tavily

        Args:
            destination: Name of destination city/country

        Returns:
            DestinationResult with comprehensive destination info
        """
        print(f"Researching destination: {destination} via Tavily...")

        if self.mock_mode:
            return self._generate_fallback_destination(destination)

        return self._search_tavily_destination(destination)

    def _search_tavily_destination(self, destination: str) -> DestinationResult:
        """Search for destination info using Tavily API"""
        try:
            from tavily import TavilyClient

            client = TavilyClient(api_key=self.config.search.tavily_api_key)

            # Search for different aspects of the destination
            info = {
                "overview": "",
                "visa": "",
                "best_time": "",
                "language": "",
                "currency": "",
                "timezone": "",
                "cultural_tips": [],
                "safety": "",
                "cuisine": [],
                "sources": []
            }

            queries = [
                (f"{destination} travel guide overview", "overview"),
                (f"{destination} visa requirements tourists", "visa"),
                (f"{destination} best time to visit weather", "best_time"),
                (f"{destination} local language currency tips", "practical"),
                (f"{destination} cultural etiquette customs tips", "culture"),
                (f"{destination} local food cuisine must try", "food"),
            ]

            for query, info_type in queries:
                try:
                    print(f"  Tavily query: {query}")
                    response = client.search(
                        query=query,
                        max_results=3,
                        search_depth="basic"
                    )

                    for result in response.get("results", []):
                        content = result.get("content", "")
                        url = result.get("url", "")

                        if url and url not in info["sources"]:
                            info["sources"].append(url)

                        if info_type == "overview" and not info["overview"]:
                            info["overview"] = content[:400] + "..." if len(content) > 400 else content

                        elif info_type == "visa":
                            visa_info = self._extract_visa_info(content)
                            if visa_info and not info["visa"]:
                                info["visa"] = visa_info

                        elif info_type == "best_time" and not info["best_time"]:
                            info["best_time"] = self._extract_best_time(content)

                        elif info_type == "practical":
                            if not info["language"]:
                                info["language"] = self._extract_language(content, destination)
                            if not info["currency"]:
                                info["currency"] = self._extract_currency(content, destination)

                        elif info_type == "culture":
                            tips = self._extract_cultural_tips(content)
                            info["cultural_tips"].extend(tips)

                        elif info_type == "food":
                            foods = self._extract_cuisine(content)
                            info["cuisine"].extend(foods)

                except Exception as e:
                    print(f"  Query failed: {str(e)}")
                    continue

            # Deduplicate and limit
            info["cultural_tips"] = list(set(info["cultural_tips"]))[:6]
            info["cuisine"] = list(set(info["cuisine"]))[:5]
            info["sources"] = info["sources"][:5]

            # Get timezone
            info["timezone"] = self._get_timezone(destination)

            # Get safety rating
            info["safety"] = self._estimate_safety_rating(destination)

            return DestinationResult(
                destination=destination,
                overview=info["overview"] or f"{destination} is a popular tourist destination.",
                visa_requirements=info["visa"] or "Check with your local embassy for visa requirements.",
                best_time_to_visit=info["best_time"] or "Research local weather patterns for best timing.",
                language=info["language"] or "Local language (English may be spoken in tourist areas)",
                currency=info["currency"] or "Check local currency before traveling",
                time_zone=info["timezone"],
                cultural_tips=info["cultural_tips"] or ["Research local customs before visiting"],
                safety_rating=info["safety"],
                local_cuisine=info["cuisine"],
                sources=info["sources"]
            )

        except Exception as e:
            print(f"Tavily destination search failed: {str(e)}")
            return self._generate_fallback_destination(destination)

    def _extract_visa_info(self, content: str) -> str:
        """Extract visa information from content"""
        visa_patterns = [
            r'visa[- ]?free.{0,50}(\d+)\s*days?',
            r'no visa required.{0,100}',
            r'visa on arrival.{0,100}',
            r'visa required.{0,100}',
        ]

        for pattern in visa_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(0)[:150]

        if "visa" in content.lower():
            # Extract sentence with visa
            sentences = content.split('.')
            for sentence in sentences:
                if "visa" in sentence.lower():
                    return sentence.strip()[:150]

        return ""

    def _extract_best_time(self, content: str) -> str:
        """Extract best time to visit from content"""
        patterns = [
            r'best time to visit.{0,150}',
            r'ideal time.{0,100}',
            r'(spring|summer|fall|autumn|winter).{0,100}(best|ideal|recommended)',
            r'(march|april|may|june|july|august|september|october|november|december).{0,100}(best|ideal)',
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(0)[:200]

        return ""

    def _extract_language(self, content: str, destination: str) -> str:
        """Extract language info"""
        lang_map = {
            "japan": "Japanese (English signage in tourist areas)",
            "tokyo": "Japanese (English signage in tourist areas)",
            "france": "French (some English in tourist areas)",
            "paris": "French (some English in tourist areas)",
            "spain": "Spanish (some English in tourist areas)",
            "thailand": "Thai (English common in tourist areas)",
            "bangkok": "Thai (English common in tourist areas)",
            "korea": "Korean (English in major cities)",
            "seoul": "Korean (English in major cities)",
            "china": "Mandarin Chinese (limited English)",
            "singapore": "English, Mandarin, Malay, Tamil",
            "vietnam": "Vietnamese (some English in tourist areas)",
        }

        for key, lang in lang_map.items():
            if key in destination.lower():
                return lang

        return "Local language - research before visiting"

    def _extract_currency(self, content: str, destination: str) -> str:
        """Extract currency info"""
        currency_map = {
            "japan": "Japanese Yen (JPY) - Many places cash only",
            "tokyo": "Japanese Yen (JPY) - Many places cash only",
            "usa": "US Dollar (USD)",
            "europe": "Euro (EUR)",
            "uk": "British Pound (GBP)",
            "thailand": "Thai Baht (THB)",
            "singapore": "Singapore Dollar (SGD)",
            "korea": "Korean Won (KRW)",
            "china": "Chinese Yuan (CNY)",
            "vietnam": "Vietnamese Dong (VND)",
            "indonesia": "Indonesian Rupiah (IDR)",
            "bali": "Indonesian Rupiah (IDR)",
        }

        for key, curr in currency_map.items():
            if key in destination.lower():
                return curr

        return "Check local currency and exchange rates"

    def _get_timezone(self, destination: str) -> str:
        """Get timezone for destination"""
        tz_map = {
            "tokyo": "JST (UTC+9)",
            "japan": "JST (UTC+9)",
            "singapore": "SGT (UTC+8)",
            "bangkok": "ICT (UTC+7)",
            "thailand": "ICT (UTC+7)",
            "london": "GMT/BST (UTC+0/+1)",
            "paris": "CET (UTC+1)",
            "new york": "EST/EDT (UTC-5/-4)",
            "los angeles": "PST/PDT (UTC-8/-7)",
            "seoul": "KST (UTC+9)",
            "hong kong": "HKT (UTC+8)",
            "sydney": "AEST (UTC+10)",
            "dubai": "GST (UTC+4)",
        }

        for key, tz in tz_map.items():
            if key in destination.lower():
                return tz

        return "Check local timezone"

    def _extract_cultural_tips(self, content: str) -> List[str]:
        """Extract cultural tips from content"""
        tips = []

        tip_patterns = [
            r"(don't|do not|avoid).{10,80}",
            r"(should|must|always).{10,80}",
            r"(tip[ping]?|bow|greeting|etiquette).{10,80}",
            r"(respect|polite|rude).{10,80}",
        ]

        for pattern in tip_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches[:2]:
                if isinstance(match, str) and len(match) > 15:
                    tips.append(match.strip()[:100])

        return tips[:4]

    def _extract_cuisine(self, content: str) -> List[str]:
        """Extract local cuisine from content"""
        foods = []

        # Look for food-related patterns
        food_patterns = [
            r"must try.{0,50}",
            r"famous for.{0,50}(food|dish|cuisine)",
            r"local (dish|food|specialty).{0,50}",
        ]

        for pattern in food_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            foods.extend(matches[:2])

        return foods[:5]

    def _estimate_safety_rating(self, destination: str) -> str:
        """Estimate safety rating based on destination"""
        very_safe = ["japan", "tokyo", "singapore", "iceland", "switzerland", "norway", "denmark"]
        safe = ["korea", "seoul", "taiwan", "australia", "new zealand", "canada", "uk", "london"]

        dest_lower = destination.lower()

        for place in very_safe:
            if place in dest_lower:
                return "Very Safe"

        for place in safe:
            if place in dest_lower:
                return "Safe"

        return "Check travel advisories"

    def _generate_fallback_destination(self, destination: str) -> DestinationResult:
        """Generate fallback destination info"""
        return DestinationResult(
            destination=destination,
            overview=f"{destination} is a popular tourist destination with diverse attractions.",
            visa_requirements="Check with your local embassy for visa requirements.",
            best_time_to_visit="Research local weather patterns for the best time to visit.",
            language=self._extract_language("", destination),
            currency=self._extract_currency("", destination),
            time_zone=self._get_timezone(destination),
            cultural_tips=[
                "Research local customs before visiting",
                "Dress respectfully at religious sites",
                "Learn basic local phrases",
                "Be aware of local tipping customs"
            ],
            safety_rating=self._estimate_safety_rating(destination),
            local_cuisine=[f"Try local {destination} cuisine"],
            sources=[]
        )

    def research_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        max_budget: Optional[float] = None,
        prefer_direct: bool = False
    ) -> FlightResearchResult:
        """
        Research available flights

        Args:
            origin: Departure city
            destination: Arrival city
            departure_date: Departure date (YYYY-MM-DD)
            return_date: Return date for round trip
            max_budget: Maximum budget per person per flight
            prefer_direct: Prefer direct flights

        Returns:
            FlightResearchResult with flight options
        """
        print(f"Researching flights: {origin} -> {destination}")

        result = self.flight_tool.search_flights(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            max_budget=max_budget,
            prefer_direct=prefer_direct
        )

        return FlightResearchResult(
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            return_date=return_date,
            outbound_options=result.get("outbound_flights", []),
            return_options=result.get("return_flights", []),
            best_outbound=result.get("best_outbound"),
            best_return=result.get("best_return"),
            total_options=result.get("total_options", 0)
        )

    def research_accommodations(
        self,
        destination: str,
        check_in: str,
        check_out: str,
        max_budget_per_night: Optional[float] = None,
        prefer_near_transport: bool = True
    ) -> AccommodationResult:
        """
        Research available accommodations

        Args:
            destination: City/location
            check_in: Check-in date
            check_out: Check-out date
            max_budget_per_night: Maximum budget per night
            prefer_near_transport: Prefer hotels near public transport

        Returns:
            AccommodationResult with hotel options
        """
        print(f"Researching accommodations in {destination}")

        result = self.hotel_tool.search_hotels(
            destination=destination,
            check_in=check_in,
            check_out=check_out,
            max_budget_per_night=max_budget_per_night,
            prefer_near_transport=prefer_near_transport
        )

        return AccommodationResult(
            destination=destination,
            check_in=check_in,
            check_out=check_out,
            hotels=result.get("hotels", []),
            best_value=result.get("best_value"),
            highest_rated=result.get("highest_rated"),
            total_options=result.get("total_options", 0)
        )

    def research_activities(
        self,
        destination: str,
        interests: Optional[List[str]] = None,
        max_budget_per_activity: Optional[float] = None
    ) -> ActivityResearchResult:
        """
        Research activities and attractions

        Args:
            destination: City/location
            interests: List of interest categories
            max_budget_per_activity: Maximum budget per activity

        Returns:
            ActivityResearchResult with activity options
        """
        print(f"Researching activities in {destination}")

        result = self.activity_tool.search_activities(
            destination=destination,
            interests=interests,
            max_budget_per_activity=max_budget_per_activity
        )

        return ActivityResearchResult(
            destination=destination,
            activities=result.get("activities", []),
            by_category=result.get("by_category", {}),
            must_do=result.get("must_do", []),
            free_activities=result.get("free_activities", []),
            total_options=result.get("total_options", 0)
        )
