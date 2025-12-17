"""
Specialized Agents for Travel Planning
Budget, Weather, Safety, and Transport analysis using Tavily
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import re

from ..utils.config import get_config
from ..tools import WeatherService


@dataclass
class BudgetOptimizationResult:
    """Result from budget optimization"""
    original_total: float
    optimized_total: float
    savings: float
    recommendations: List[Dict[str, Any]]
    budget_friendly_alternatives: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "original_total": self.original_total,
            "optimized_total": self.optimized_total,
            "savings": self.savings,
            "recommendations": self.recommendations,
            "budget_friendly_alternatives": self.budget_friendly_alternatives
        }


@dataclass
class WeatherAnalysisResult:
    """Result from weather analysis"""
    destination: str
    travel_dates: str
    daily_forecast: List[Dict[str, Any]]
    summary: Dict[str, Any]
    packing_suggestions: List[str]
    weather_advisory: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "destination": self.destination,
            "travel_dates": self.travel_dates,
            "daily_forecast": self.daily_forecast,
            "summary": self.summary,
            "packing_suggestions": self.packing_suggestions,
            "weather_advisory": self.weather_advisory
        }


@dataclass
class SafetyAnalysisResult:
    """Result from safety analysis"""
    destination: str
    overall_safety_rating: str
    safety_tips: List[str]
    areas_to_avoid: List[str]
    emergency_contacts: Dict[str, str]
    health_advisories: List[str]
    scam_warnings: List[str]
    sources: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "destination": self.destination,
            "overall_safety_rating": self.overall_safety_rating,
            "safety_tips": self.safety_tips,
            "areas_to_avoid": self.areas_to_avoid,
            "emergency_contacts": self.emergency_contacts,
            "health_advisories": self.health_advisories,
            "scam_warnings": self.scam_warnings,
            "sources": self.sources
        }


@dataclass
class TransportAnalysisResult:
    """Result from local transport analysis"""
    destination: str
    transport_options: List[Dict[str, Any]]
    recommended_passes: List[Dict[str, Any]]
    airport_transfer: Dict[str, Any]
    tips: List[str]
    sources: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "destination": self.destination,
            "transport_options": self.transport_options,
            "recommended_passes": self.recommended_passes,
            "airport_transfer": self.airport_transfer,
            "tips": self.tips,
            "sources": self.sources
        }


class BudgetAgent:
    """Agent for budget optimization"""

    def __init__(self, config=None):
        self.config = config or get_config()

    def optimize_budget(
        self,
        current_selections: Dict[str, Any],
        budget_limit: float,
        priorities: Optional[List[str]] = None
    ) -> BudgetOptimizationResult:
        """
        Optimize selections to fit within budget

        Args:
            current_selections: Current flight, hotel, activity selections
            budget_limit: Maximum budget
            priorities: What to prioritize (e.g., ["accommodation", "experiences"])

        Returns:
            BudgetOptimizationResult with optimized selections
        """
        print(f"Optimizing budget (limit: ${budget_limit})")

        # Calculate current total
        flights = current_selections.get("flights", {})
        hotels = current_selections.get("hotels", {})
        activities = current_selections.get("activities", [])
        num_days = current_selections.get("num_days", 5)

        flight_cost = flights.get("price", 0) * 2  # Round trip
        hotel_cost = hotels.get("price_per_night", 0) * (num_days - 1)
        activity_cost = sum(a.get("price", 0) for a in activities)

        # Estimate daily misc cost based on destination cost level
        daily_misc = self._estimate_daily_misc(activities)
        misc_cost = daily_misc * num_days

        original_total = flight_cost + hotel_cost + activity_cost + misc_cost

        recommendations = []
        alternatives = []

        # Suggest budget alternatives based on actual costs
        if flight_cost > budget_limit * 0.35:
            potential_savings = flight_cost * 0.3
            recommendations.append({
                "category": "flights",
                "suggestion": "Consider budget airlines or flexible dates",
                "current_cost": flight_cost,
                "potential_savings": potential_savings
            })

        if hotel_cost > budget_limit * 0.25:
            potential_savings = hotel_cost * 0.4
            recommendations.append({
                "category": "accommodation",
                "suggestion": "Consider business hotels, hostels, or apartments",
                "current_cost": hotel_cost,
                "potential_savings": potential_savings
            })
            alternatives.append({
                "type": "accommodation",
                "name": "Business Hotel or Hostel",
                "estimated_price_per_night": hotels.get("price_per_night", 100) * 0.5,
                "note": "Clean, safe, often near stations"
            })

        if activity_cost > budget_limit * 0.15:
            potential_savings = activity_cost * 0.5
            recommendations.append({
                "category": "activities",
                "suggestion": "Many attractions are free - temples, parks, markets, walking tours",
                "current_cost": activity_cost,
                "potential_savings": potential_savings
            })
            alternatives.append({
                "type": "activity",
                "name": "Free walking tours and public attractions",
                "price": 0,
                "note": "Tip-based tours often available"
            })

        # Calculate optimized total
        potential_savings = sum(r.get("potential_savings", 0) for r in recommendations)
        optimized_total = max(original_total - potential_savings, original_total * 0.6)

        return BudgetOptimizationResult(
            original_total=round(original_total, 2),
            optimized_total=round(optimized_total, 2),
            savings=round(potential_savings, 2),
            recommendations=recommendations,
            budget_friendly_alternatives=alternatives
        )

    def _estimate_daily_misc(self, activities: List) -> float:
        """Estimate daily misc cost based on activities price level"""
        if activities:
            avg_price = sum(a.get("price", 0) for a in activities) / len(activities)
            if avg_price > 50:
                return 80  # Expensive destination
            elif avg_price > 20:
                return 50  # Moderate
            else:
                return 35  # Budget
        return 50  # Default


class WeatherAgent:
    """Agent for weather analysis"""

    def __init__(self, config=None):
        self.config = config or get_config()
        self.weather_service = WeatherService()

    def analyze_weather(
        self,
        destination: str,
        start_date: str,
        num_days: int = 7
    ) -> WeatherAnalysisResult:
        """
        Analyze weather for the trip

        Args:
            destination: Destination city
            start_date: Trip start date
            num_days: Number of days

        Returns:
            WeatherAnalysisResult with forecast and recommendations
        """
        print(f"Analyzing weather for {destination}")

        forecast = self.weather_service.get_forecast(
            destination=destination,
            start_date=start_date,
            num_days=num_days
        )

        # Generate weather advisory
        avg_rain = forecast["summary"]["average_rain_chance"]
        avg_high = forecast["summary"]["average_high"]

        if avg_rain > 50:
            advisory = "High chance of rain - plan indoor alternatives and carry rain gear"
        elif avg_high > 32:
            advisory = "Hot weather expected - stay hydrated, plan activities for cooler parts of day"
        elif avg_high < 10:
            advisory = "Cold weather expected - pack warm layers"
        else:
            advisory = "Pleasant weather expected - great conditions for sightseeing"

        return WeatherAnalysisResult(
            destination=destination,
            travel_dates=f"{start_date} ({num_days} days)",
            daily_forecast=forecast["daily_forecast"],
            summary=forecast["summary"],
            packing_suggestions=forecast["packing_suggestions"],
            weather_advisory=advisory
        )


class SafetyAgent:
    """Agent for safety analysis using Tavily"""

    # Emergency contacts by country (kept as reference data)
    EMERGENCY_CONTACTS = {
        "japan": {"Police": "110", "Ambulance/Fire": "119", "Tourist Helpline": "03-5321-3077"},
        "usa": {"Emergency": "911", "Non-emergency police": "311"},
        "uk": {"Emergency": "999", "Non-emergency": "101"},
        "australia": {"Emergency": "000"},
        "singapore": {"Emergency": "999", "Ambulance": "995"},
        "thailand": {"Police": "191", "Tourist Police": "1155", "Ambulance": "1669"},
        "korea": {"Emergency": "112", "Fire/Ambulance": "119"},
        "default": {"International Emergency": "112"}
    }

    def __init__(self, config=None):
        self.config = config or get_config()
        self.mock_mode = self.config.app.mock_external_apis

        if not self.config.search.tavily_api_key:
            self.mock_mode = True
            print("Tavily key not found - using fallback for safety analysis")
        else:
            print(f"SafetyAgent initialized with Tavily (mock_mode: {self.mock_mode})")

    def analyze_safety(self, destination: str) -> SafetyAnalysisResult:
        """
        Analyze safety for the destination using Tavily

        Args:
            destination: Destination city/country

        Returns:
            SafetyAnalysisResult with safety information
        """
        print(f"Analyzing safety for {destination} via Tavily...")

        if self.mock_mode:
            return self._generate_fallback_safety(destination)

        return self._search_tavily_safety(destination)

    def _search_tavily_safety(self, destination: str) -> SafetyAnalysisResult:
        """Search for safety info using Tavily API"""
        try:
            from tavily import TavilyClient

            client = TavilyClient(api_key=self.config.search.tavily_api_key)

            safety_info = {
                "tips": [],
                "areas_to_avoid": [],
                "health": [],
                "scams": [],
                "sources": []
            }

            queries = [
                (f"{destination} travel safety tips tourists", "tips"),
                (f"{destination} areas to avoid dangerous neighborhoods", "areas"),
                (f"{destination} tourist scams warnings", "scams"),
                (f"{destination} health travel advice vaccinations", "health"),
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

                        if url and url not in safety_info["sources"]:
                            safety_info["sources"].append(url)

                        if info_type == "tips":
                            tips = self._extract_safety_tips(content)
                            safety_info["tips"].extend(tips)

                        elif info_type == "areas":
                            areas = self._extract_areas_to_avoid(content)
                            safety_info["areas_to_avoid"].extend(areas)

                        elif info_type == "scams":
                            scams = self._extract_scam_warnings(content)
                            safety_info["scams"].extend(scams)

                        elif info_type == "health":
                            health = self._extract_health_info(content)
                            safety_info["health"].extend(health)

                except Exception as e:
                    print(f"  Query failed: {str(e)}")
                    continue

            # Deduplicate and limit
            safety_info["tips"] = list(set(safety_info["tips"]))[:6]
            safety_info["areas_to_avoid"] = list(set(safety_info["areas_to_avoid"]))[:4]
            safety_info["scams"] = list(set(safety_info["scams"]))[:4]
            safety_info["health"] = list(set(safety_info["health"]))[:4]
            safety_info["sources"] = safety_info["sources"][:5]

            # Get emergency contacts
            emergency = self._get_emergency_contacts(destination)

            # Estimate safety rating
            rating = self._estimate_safety_rating(destination)

            return SafetyAnalysisResult(
                destination=destination,
                overall_safety_rating=rating,
                safety_tips=safety_info["tips"] or ["Stay aware of surroundings", "Keep valuables secure"],
                areas_to_avoid=safety_info["areas_to_avoid"] or ["Research locally upon arrival"],
                emergency_contacts=emergency,
                health_advisories=safety_info["health"] or ["Check travel health recommendations"],
                scam_warnings=safety_info["scams"] or ["Be wary of common tourist scams"],
                sources=safety_info["sources"]
            )

        except Exception as e:
            print(f"Tavily safety search failed: {str(e)}")
            return self._generate_fallback_safety(destination)

    def _extract_safety_tips(self, content: str) -> List[str]:
        """Extract safety tips from content"""
        tips = []
        patterns = [
            r"(be careful|watch out|avoid|don't|do not).{10,80}",
            r"(keep|store|secure).{10,60}(valuables|belongings|passport)",
            r"(safe|safety).{10,80}",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches[:2]:
                if isinstance(match, tuple):
                    match = " ".join(match)
                if len(match) > 15:
                    tips.append(match.strip()[:100])

        return tips[:4]

    def _extract_areas_to_avoid(self, content: str) -> List[str]:
        """Extract areas to avoid from content"""
        areas = []
        patterns = [
            r"avoid.{0,20}(area|neighborhood|district|street).{0,50}",
            r"(dangerous|sketchy|unsafe).{0,20}(area|neighborhood|district)",
            r"at night.{0,50}(avoid|dangerous|unsafe)",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches[:2]:
                if isinstance(match, tuple):
                    match = " ".join(match)
                if len(match) > 10:
                    areas.append(match.strip()[:80])

        return areas[:3]

    def _extract_scam_warnings(self, content: str) -> List[str]:
        """Extract scam warnings from content"""
        scams = []
        patterns = [
            r"scam.{0,80}",
            r"(overcharge|overpriced|rip-?off).{0,60}",
            r"(fake|fraudulent|unlicensed).{0,60}",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches[:2]:
                if len(match) > 15:
                    scams.append(match.strip()[:100])

        return scams[:3]

    def _extract_health_info(self, content: str) -> List[str]:
        """Extract health information from content"""
        health = []
        patterns = [
            r"(vaccin|immuniz).{0,80}",
            r"tap water.{0,50}(safe|not safe|drink|avoid)",
            r"(hospital|pharmacy|medical).{0,60}",
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches[:2]:
                if len(match) > 10:
                    health.append(match.strip()[:80])

        return health[:3]

    def _get_emergency_contacts(self, destination: str) -> Dict[str, str]:
        """Get emergency contacts for destination"""
        dest_lower = destination.lower()

        for country, contacts in self.EMERGENCY_CONTACTS.items():
            if country in dest_lower:
                return contacts

        return self.EMERGENCY_CONTACTS["default"]

    def _estimate_safety_rating(self, destination: str) -> str:
        """Estimate safety rating"""
        very_safe = ["japan", "tokyo", "singapore", "iceland", "switzerland", "norway", "denmark", "new zealand"]
        safe = ["korea", "seoul", "taiwan", "australia", "canada", "uk", "london", "germany"]

        dest_lower = destination.lower()

        for place in very_safe:
            if place in dest_lower:
                return "Very Safe"

        for place in safe:
            if place in dest_lower:
                return "Safe"

        return "Check travel advisories"

    def _generate_fallback_safety(self, destination: str) -> SafetyAnalysisResult:
        """Generate fallback safety info"""
        return SafetyAnalysisResult(
            destination=destination,
            overall_safety_rating=self._estimate_safety_rating(destination),
            safety_tips=[
                "Research destination-specific safety before traveling",
                "Keep copies of important documents",
                "Stay aware of your surroundings",
                "Use hotel safes for valuables",
                "Register with your embassy"
            ],
            areas_to_avoid=["Research locally upon arrival"],
            emergency_contacts=self._get_emergency_contacts(destination),
            health_advisories=["Consult travel health clinic before departure"],
            scam_warnings=["Be wary of common tourist scams"],
            sources=[]
        )


class TransportAgent:
    """Agent for local transport analysis using Tavily"""

    def __init__(self, config=None):
        self.config = config or get_config()
        self.mock_mode = self.config.app.mock_external_apis

        if not self.config.search.tavily_api_key:
            self.mock_mode = True
            print("Tavily key not found - using fallback for transport analysis")
        else:
            print(f"TransportAgent initialized with Tavily (mock_mode: {self.mock_mode})")

    def analyze_local_transport(self, destination: str) -> TransportAnalysisResult:
        """
        Analyze local transport options using Tavily

        Args:
            destination: Destination city

        Returns:
            TransportAnalysisResult with transport information
        """
        print(f"Analyzing transport for {destination} via Tavily...")

        if self.mock_mode:
            return self._generate_fallback_transport(destination)

        return self._search_tavily_transport(destination)

    def _search_tavily_transport(self, destination: str) -> TransportAnalysisResult:
        """Search for transport info using Tavily API"""
        try:
            from tavily import TavilyClient

            client = TavilyClient(api_key=self.config.search.tavily_api_key)

            transport_info = {
                "options": [],
                "passes": [],
                "airport": {},
                "tips": [],
                "sources": []
            }

            queries = [
                (f"{destination} public transport metro subway guide", "transport"),
                (f"{destination} tourist transport pass card", "passes"),
                (f"{destination} airport to city center transfer options", "airport"),
                (f"{destination} getting around tips tourists", "tips"),
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

                        if url and url not in transport_info["sources"]:
                            transport_info["sources"].append(url)

                        if info_type == "transport":
                            options = self._extract_transport_options(content)
                            transport_info["options"].extend(options)

                        elif info_type == "passes":
                            passes = self._extract_transport_passes(content, destination)
                            transport_info["passes"].extend(passes)

                        elif info_type == "airport":
                            airport = self._extract_airport_transfer(content, destination)
                            if airport and not transport_info["airport"]:
                                transport_info["airport"] = airport

                        elif info_type == "tips":
                            tips = self._extract_transport_tips(content)
                            transport_info["tips"].extend(tips)

                except Exception as e:
                    print(f"  Query failed: {str(e)}")
                    continue

            # Deduplicate and limit
            transport_info["options"] = transport_info["options"][:5]
            transport_info["passes"] = transport_info["passes"][:4]
            transport_info["tips"] = list(set(transport_info["tips"]))[:5]
            transport_info["sources"] = transport_info["sources"][:5]

            # Ensure we have airport transfer info
            if not transport_info["airport"]:
                transport_info["airport"] = {"recommendation": "Research options before arrival"}

            return TransportAnalysisResult(
                destination=destination,
                transport_options=transport_info["options"] or self._get_fallback_options(destination),
                recommended_passes=transport_info["passes"] or [{"name": "Tourist Pass", "note": "Check availability"}],
                airport_transfer=transport_info["airport"],
                tips=transport_info["tips"] or ["Download offline maps", "Research transport before arriving"],
                sources=transport_info["sources"]
            )

        except Exception as e:
            print(f"Tavily transport search failed: {str(e)}")
            return self._generate_fallback_transport(destination)

    def _extract_transport_options(self, content: str) -> List[Dict]:
        """Extract transport options from content"""
        options = []

        transport_types = ["metro", "subway", "bus", "train", "tram", "taxi", "uber", "grab"]

        for transport in transport_types:
            if transport in content.lower():
                # Extract some context around the transport mention
                pattern = rf'{transport}.{{0,100}}'
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    options.append({
                        "type": transport.capitalize(),
                        "coverage": match.group(0)[:100],
                        "ease_of_use": "Check local guides"
                    })

        return options[:4]

    def _extract_transport_passes(self, content: str, destination: str) -> List[Dict]:
        """Extract transport pass information"""
        passes = []

        pass_patterns = [
            r'(\w+\s*pass|card).{0,80}',
            r'(unlimited|day pass|tourist).{0,60}',
        ]

        for pattern in pass_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches[:2]:
                if len(match) > 5:
                    passes.append({
                        "name": match.strip()[:50],
                        "note": "Check current prices and availability"
                    })

        return passes[:3]

    def _extract_airport_transfer(self, content: str, destination: str) -> Dict:
        """Extract airport transfer information"""
        info = {"from": f"Airport", "options": [], "recommendation": ""}

        # Look for airport-related info
        airport_patterns = [
            r'(airport|terminal).{0,100}(train|bus|taxi|shuttle)',
            r'(\d+)\s*(minutes?|mins?|hours?).{0,50}(center|city)',
        ]

        options = []
        for pattern in airport_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches[:3]:
                if isinstance(match, tuple):
                    match = " ".join(match)
                options.append({"method": match[:60], "note": "Check current schedules"})

        info["options"] = options[:3]
        info["recommendation"] = "Research current options and book in advance if needed"

        return info

    def _extract_transport_tips(self, content: str) -> List[str]:
        """Extract transport tips"""
        tips = []

        tip_patterns = [
            r'(avoid|don\'t|tip).{10,80}',
            r'(rush hour|peak).{0,60}',
            r'(google maps|app|card).{0,60}(recommend|useful|download)',
        ]

        for pattern in tip_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            for match in matches[:2]:
                if isinstance(match, tuple):
                    match = " ".join(match)
                if len(match) > 15:
                    tips.append(match.strip()[:80])

        return tips[:4]

    def _get_fallback_options(self, destination: str) -> List[Dict]:
        """Get fallback transport options"""
        return [
            {
                "type": "Public Transport",
                "coverage": "Check local metro/bus systems",
                "ease_of_use": "Research before arrival"
            },
            {
                "type": "Taxi/Ride-share",
                "coverage": "Usually available",
                "ease_of_use": "Download local apps"
            }
        ]

    def _generate_fallback_transport(self, destination: str) -> TransportAnalysisResult:
        """Generate fallback transport info"""
        return TransportAnalysisResult(
            destination=destination,
            transport_options=self._get_fallback_options(destination),
            recommended_passes=[
                {
                    "name": "Tourist Transport Pass",
                    "note": "Check if available for your destination"
                }
            ],
            airport_transfer={
                "recommendation": "Research airport transfer options before arrival"
            },
            tips=[
                "Research local transport before arriving",
                "Download offline maps",
                "Get a local transport card if available",
                "Keep small bills/coins for fare"
            ],
            sources=[]
        )
