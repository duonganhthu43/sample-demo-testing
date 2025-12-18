"""
Specialized Agents for Travel Planning
Budget, Weather, Safety, and Transport analysis using Tavily + LLM
"""

import json
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

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


# LLM System Prompts

BUDGET_OPTIMIZATION_PROMPT = """You are a travel budget optimization expert. Analyze the current travel selections and provide intelligent budget optimization recommendations.

## Input
You will receive current travel selections (flights, hotels, activities) and budget constraints.

## Output Format
Return a valid JSON object:
```json
{
    "original_total": 1500.00,
    "optimized_total": 1200.00,
    "savings": 300.00,
    "recommendations": [
        {
            "category": "flights",
            "suggestion": "Specific actionable suggestion",
            "current_cost": 500.00,
            "potential_savings": 100.00
        }
    ],
    "budget_friendly_alternatives": [
        {
            "type": "accommodation",
            "name": "Alternative option name",
            "estimated_price": 80.00,
            "note": "Why this is a good alternative"
        }
    ]
}
```

## Guidelines:
1. Calculate actual costs from provided data
2. Estimate destination-specific daily costs (food, transport, misc) based on cost of living
3. Provide specific, actionable recommendations
4. Suggest realistic alternatives that maintain quality
5. Consider the destination's typical prices

IMPORTANT: Return ONLY the JSON object, no markdown formatting or explanation."""


WEATHER_ANALYSIS_PROMPT = """You are a travel weather analyst. Analyze weather data and provide actionable recommendations for travelers.

## Input
You will receive weather forecast data for a destination.

## Output Format
Return a valid JSON object:
```json
{
    "weather_advisory": "Comprehensive weather advisory for the trip",
    "packing_suggestions": [
        "Specific item 1",
        "Specific item 2",
        "Specific item 3"
    ],
    "activity_recommendations": "How weather affects planned activities"
}
```

## Guidelines:
1. Provide specific, actionable packing suggestions based on the forecast
2. Consider temperature ranges, precipitation, humidity
3. Suggest appropriate clothing layers
4. Warn about any extreme conditions
5. Recommend best times of day for outdoor activities

IMPORTANT: Return ONLY the JSON object, no markdown formatting or explanation."""


SAFETY_EXTRACTION_PROMPT = """You are a travel safety expert. Extract and analyze safety information from search results.

## Input
You will receive search results about a destination's safety.

## Output Format
Return a valid JSON object:
```json
{
    "overall_safety_rating": "Very Safe / Safe / Moderate / Exercise Caution",
    "safety_tips": ["Tip 1", "Tip 2", "Tip 3", "Tip 4"],
    "areas_to_avoid": ["Area 1", "Area 2"],
    "emergency_contacts": {
        "Police": "number",
        "Ambulance": "number",
        "Tourist Helpline": "number"
    },
    "health_advisories": ["Advisory 1", "Advisory 2"],
    "scam_warnings": ["Warning 1", "Warning 2"]
}
```

## Guidelines:
1. Extract specific, actionable safety tips
2. List specific areas or neighborhoods to avoid
3. Include accurate emergency numbers for the destination
4. Note any required vaccinations or health precautions
5. List common tourist scams specific to this destination
6. Base safety rating on actual data, not assumptions

IMPORTANT: Return ONLY the JSON object, no markdown formatting or explanation."""


TRANSPORT_EXTRACTION_PROMPT = """You are a local transport expert. Extract and analyze transport information from search results.

## Input
You will receive search results about a destination's transport options.

## Output Format
Return a valid JSON object:
```json
{
    "transport_options": [
        {
            "type": "Metro/Subway",
            "coverage": "Description of coverage",
            "ease_of_use": "Easy/Moderate/Complex",
            "cost_range": "Price range"
        }
    ],
    "recommended_passes": [
        {
            "name": "Pass name",
            "price": "Price if known",
            "duration": "1 day / 3 days / etc",
            "note": "What it includes"
        }
    ],
    "airport_transfer": {
        "best_option": "Recommended option",
        "duration": "Time to city center",
        "cost": "Estimated cost",
        "alternatives": ["Option 1", "Option 2"]
    },
    "tips": ["Tip 1", "Tip 2", "Tip 3"]
}
```

## Guidelines:
1. List all major transport options available
2. Recommend best value tourist passes
3. Provide specific airport transfer options with costs
4. Include practical tips for using local transport
5. Note any apps or cards travelers should get

IMPORTANT: Return ONLY the JSON object, no markdown formatting or explanation."""


class BudgetAgent:
    """Agent for budget optimization using LLM"""

    def __init__(self, config=None):
        self.config = config or get_config()

    def optimize_budget(
        self,
        current_selections: Dict[str, Any],
        budget_limit: float,
        priorities: Optional[List[str]] = None
    ) -> BudgetOptimizationResult:
        """
        Optimize selections to fit within budget using LLM

        Args:
            current_selections: Current flight, hotel, activity selections
            budget_limit: Maximum budget
            priorities: What to prioritize

        Returns:
            BudgetOptimizationResult with optimized selections
        """
        print(f"Optimizing budget with LLM (limit: ${budget_limit})")

        # Prepare context for LLM
        context = self._prepare_budget_context(current_selections, budget_limit, priorities)

        # Get LLM client
        client = self.config.get_llm_client(label="budget_agent")

        try:
            response = client.chat.completions.create(
                model=self.config.llm.model,
                messages=[
                    {
                        "role": "system",
                        "content": BUDGET_OPTIMIZATION_PROMPT
                    },
                    {
                        "role": "user",
                        "content": f"Optimize this travel budget:\n\n{context}"
                    }
                ],
                temperature=0.3,
                max_tokens=2000
            )

            content = response.choices[0].message.content
            data = self._parse_llm_response(content)

            print("Budget optimization completed successfully")

            return BudgetOptimizationResult(
                original_total=data.get("original_total", 0),
                optimized_total=data.get("optimized_total", 0),
                savings=data.get("savings", 0),
                recommendations=data.get("recommendations", []),
                budget_friendly_alternatives=data.get("budget_friendly_alternatives", [])
            )

        except Exception as e:
            print(f"LLM budget optimization failed: {str(e)}")
            return self._fallback_optimize(current_selections, budget_limit)

    def _prepare_budget_context(
        self,
        current_selections: Dict,
        budget_limit: float,
        priorities: Optional[List[str]]
    ) -> str:
        """Prepare context for budget optimization"""
        sections = []

        sections.append("## BUDGET LIMIT")
        sections.append(f"Maximum budget: ${budget_limit}")

        if priorities:
            sections.append(f"\nPriorities: {priorities}")

        sections.append("\n## CURRENT SELECTIONS")
        sections.append(json.dumps(self._sanitize_for_llm(current_selections), indent=2, default=str))

        return "\n".join(sections)

    def _sanitize_for_llm(self, data: Any) -> Any:
        if isinstance(data, dict):
            sanitized: Dict[str, Any] = {}
            for key, value in data.items():
                if key == "image_base64":
                    if value:
                        sanitized["has_image"] = True
                    continue
                sanitized[key] = self._sanitize_for_llm(value)
            return sanitized

        if isinstance(data, list):
            if len(data) > 30:
                data = data[:30]
            return [self._sanitize_for_llm(item) for item in data]

        if isinstance(data, str):
            if len(data) > 2000:
                return data[:2000] + "..."
            return data

        return data

    def _parse_llm_response(self, content: str) -> Dict[str, Any]:
        """Parse LLM JSON response"""
        try:
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            return json.loads(content.strip())
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            return {}

    def _fallback_optimize(
        self,
        current_selections: Dict,
        budget_limit: float
    ) -> BudgetOptimizationResult:
        """Fallback optimization if LLM fails"""
        flights = current_selections.get("flights", {})
        hotels = current_selections.get("hotels", {})
        activities = current_selections.get("activities", [])
        num_days = current_selections.get("num_days", 5)

        flight_cost = flights.get("price", 0) * 2
        hotel_cost = hotels.get("price_per_night", 0) * (num_days - 1)
        activity_cost = sum(a.get("price", 0) for a in activities)

        original_total = flight_cost + hotel_cost + activity_cost

        return BudgetOptimizationResult(
            original_total=round(original_total, 2),
            optimized_total=round(original_total, 2),
            savings=0,
            recommendations=[{"suggestion": "Review options manually"}],
            budget_friendly_alternatives=[]
        )


class WeatherAgent:
    """Agent for weather analysis using LLM"""

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
        Analyze weather for the trip using LLM

        Args:
            destination: Destination city
            start_date: Trip start date
            num_days: Number of days

        Returns:
            WeatherAnalysisResult with forecast and recommendations
        """
        print(f"Analyzing weather for {destination} with LLM")

        # Get weather forecast data
        forecast = self.weather_service.get_forecast(
            destination=destination,
            start_date=start_date,
            num_days=num_days
        )

        # Use LLM to generate intelligent advisory and packing suggestions
        context = self._prepare_weather_context(destination, forecast, num_days)

        client = self.config.get_llm_client(label="weather_agent")

        try:
            response = client.chat.completions.create(
                model=self.config.llm.model,
                messages=[
                    {
                        "role": "system",
                        "content": WEATHER_ANALYSIS_PROMPT
                    },
                    {
                        "role": "user",
                        "content": f"Analyze this weather forecast and provide recommendations:\n\n{context}"
                    }
                ],
                temperature=0.3,
                max_tokens=1500
            )

            content = response.choices[0].message.content
            data = self._parse_llm_response(content)

            print("Weather analysis completed successfully")

            return WeatherAnalysisResult(
                destination=destination,
                travel_dates=f"{start_date} ({num_days} days)",
                daily_forecast=forecast["daily_forecast"],
                summary=forecast["summary"],
                packing_suggestions=data.get("packing_suggestions", forecast["packing_suggestions"]),
                weather_advisory=data.get("weather_advisory", "Check local forecast")
            )

        except Exception as e:
            print(f"LLM weather analysis failed: {str(e)}")
            return WeatherAnalysisResult(
                destination=destination,
                travel_dates=f"{start_date} ({num_days} days)",
                daily_forecast=forecast["daily_forecast"],
                summary=forecast["summary"],
                packing_suggestions=forecast["packing_suggestions"],
                weather_advisory="Check local weather forecast before departure"
            )

    def _prepare_weather_context(self, destination: str, forecast: Dict, num_days: int) -> str:
        """Prepare context for weather analysis"""
        sections = []

        sections.append(f"## DESTINATION: {destination}")
        sections.append(f"Trip duration: {num_days} days")

        sections.append("\n## WEATHER SUMMARY")
        sections.append(json.dumps(forecast["summary"], indent=2))

        sections.append("\n## DAILY FORECAST")
        sections.append(json.dumps(forecast["daily_forecast"], indent=2))

        return "\n".join(sections)

    def _parse_llm_response(self, content: str) -> Dict[str, Any]:
        """Parse LLM JSON response"""
        try:
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            return json.loads(content.strip())
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            return {}


class SafetyAgent:
    """Agent for safety analysis using Tavily + LLM"""

    def __init__(self, config=None):
        self.config = config or get_config()

        if not self.config.search.tavily_api_key and not self.config.app.mock_external_apis:
            raise ValueError("TAVILY_API_KEY is required when MOCK_EXTERNAL_APIS=false")

        if self.config.search.tavily_api_key:
            print("SafetyAgent initialized with Tavily + LLM")
        else:
            print("Warning: Tavily API key not found - will use LLM only")

    def analyze_safety(self, destination: str) -> SafetyAnalysisResult:
        """
        Analyze safety for the destination using Tavily + LLM

        Args:
            destination: Destination city/country

        Returns:
            SafetyAnalysisResult with safety information
        """
        print(f"Analyzing safety for {destination} via Tavily + LLM...")

        return self._search_and_analyze_safety(destination)

    def _search_and_analyze_safety(self, destination: str) -> SafetyAnalysisResult:
        """Search for safety info using Tavily API and analyze with LLM"""
        all_content = []
        sources = []

        # Try to get Tavily results
        try:
            from tavily import TavilyClient

            if self.config.search.tavily_api_key:
                client = TavilyClient(api_key=self.config.search.tavily_api_key)

                queries = [
                    f"{destination} travel safety tips tourists",
                    f"{destination} areas to avoid dangerous neighborhoods",
                    f"{destination} tourist scams warnings",
                    f"{destination} emergency numbers police ambulance",
                    f"{destination} health travel advice",
                ]

                for query in queries:
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

                            if content:
                                all_content.append(content)
                            if url and url not in sources:
                                sources.append(url)

                    except Exception as e:
                        print(f"  Query failed: {str(e)}")
                        continue

        except Exception as e:
            print(f"Tavily search failed: {str(e)}")

        if not self.config.app.mock_external_apis and not all_content:
            raise ValueError("Failed to fetch safety information from Tavily (no results).")

        # Use LLM to extract structured safety info
        extracted = self._extract_with_llm(destination, all_content)

        return SafetyAnalysisResult(
            destination=destination,
            overall_safety_rating=extracted.get("overall_safety_rating", "Check travel advisories"),
            safety_tips=extracted.get("safety_tips", ["Research safety before traveling"]),
            areas_to_avoid=extracted.get("areas_to_avoid", ["Research locally"]),
            emergency_contacts=extracted.get("emergency_contacts", {"Emergency": "Check local numbers"}),
            health_advisories=extracted.get("health_advisories", ["Consult travel health clinic"]),
            scam_warnings=extracted.get("scam_warnings", ["Be wary of common tourist scams"]),
            sources=sources[:5]
        )

    def _extract_with_llm(self, destination: str, content_list: List[str]) -> Dict[str, Any]:
        """Use LLM to extract structured safety info"""
        try:
            client = self.config.get_llm_client(label="safety_agent")

            if content_list:
                combined_content = "\n\n---\n\n".join(content_list[:10])
                if len(combined_content) > 8000:
                    combined_content = combined_content[:8000] + "..."
                prompt = f"Extract safety information for {destination} from these search results:\n\n{combined_content}"
            else:
                prompt = f"Based on your knowledge, provide safety information for {destination}. Include emergency contacts, safety tips, areas to avoid, health advisories, and scam warnings."

            response = client.chat.completions.create(
                model=self.config.llm.model,
                messages=[
                    {
                        "role": "system",
                        "content": SAFETY_EXTRACTION_PROMPT
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
                max_tokens=2000
            )

            content = response.choices[0].message.content
            return self._parse_llm_response(content)

        except Exception as e:
            print(f"LLM extraction failed: {str(e)}")
            return {}

    def _parse_llm_response(self, content: str) -> Dict[str, Any]:
        """Parse LLM JSON response"""
        try:
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            return json.loads(content.strip())
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            return {}


class TransportAgent:
    """Agent for local transport analysis using Tavily + LLM"""

    def __init__(self, config=None):
        self.config = config or get_config()

        if not self.config.search.tavily_api_key and not self.config.app.mock_external_apis:
            raise ValueError("TAVILY_API_KEY is required when MOCK_EXTERNAL_APIS=false")

        if self.config.search.tavily_api_key:
            print("TransportAgent initialized with Tavily + LLM")
        else:
            print("Warning: Tavily API key not found - will use LLM only")

    def analyze_local_transport(self, destination: str) -> TransportAnalysisResult:
        """
        Analyze local transport options using Tavily + LLM

        Args:
            destination: Destination city

        Returns:
            TransportAnalysisResult with transport information
        """
        print(f"Analyzing transport for {destination} via Tavily + LLM...")

        return self._search_and_analyze_transport(destination)

    def _search_and_analyze_transport(self, destination: str) -> TransportAnalysisResult:
        """Search for transport info using Tavily API and analyze with LLM"""
        all_content = []
        sources = []

        # Try to get Tavily results
        try:
            from tavily import TavilyClient

            if self.config.search.tavily_api_key:
                client = TavilyClient(api_key=self.config.search.tavily_api_key)

                queries = [
                    f"{destination} public transport metro subway bus guide",
                    f"{destination} tourist transport pass card unlimited",
                    f"{destination} airport to city center transfer options",
                    f"{destination} getting around tips tourists",
                ]

                for query in queries:
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

                            if content:
                                all_content.append(content)
                            if url and url not in sources:
                                sources.append(url)

                    except Exception as e:
                        print(f"  Query failed: {str(e)}")
                        continue

        except Exception as e:
            print(f"Tavily search failed: {str(e)}")

        if not self.config.app.mock_external_apis and not all_content:
            raise ValueError("Failed to fetch transport information from Tavily (no results).")

        # Use LLM to extract structured transport info
        extracted = self._extract_with_llm(destination, all_content)

        return TransportAnalysisResult(
            destination=destination,
            transport_options=extracted.get("transport_options", [{"type": "Public Transport", "note": "Research options"}]),
            recommended_passes=extracted.get("recommended_passes", [{"name": "Tourist Pass", "note": "Check availability"}]),
            airport_transfer=extracted.get("airport_transfer", {"recommendation": "Research before arrival"}),
            tips=extracted.get("tips", ["Download offline maps", "Get local transport card"]),
            sources=sources[:5]
        )

    def _extract_with_llm(self, destination: str, content_list: List[str]) -> Dict[str, Any]:
        """Use LLM to extract structured transport info"""
        try:
            client = self.config.get_llm_client(label="transport_agent")

            if content_list:
                combined_content = "\n\n---\n\n".join(content_list[:10])
                if len(combined_content) > 8000:
                    combined_content = combined_content[:8000] + "..."
                prompt = f"Extract transport information for {destination} from these search results:\n\n{combined_content}"
            else:
                prompt = f"Based on your knowledge, provide transport information for {destination}. Include public transport options, tourist passes, airport transfer options, and practical tips."

            response = client.chat.completions.create(
                model=self.config.llm.model,
                messages=[
                    {
                        "role": "system",
                        "content": TRANSPORT_EXTRACTION_PROMPT
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
                max_tokens=2000
            )

            content = response.choices[0].message.content
            return self._parse_llm_response(content)

        except Exception as e:
            print(f"LLM extraction failed: {str(e)}")
            return {}

    def _parse_llm_response(self, content: str) -> Dict[str, Any]:
        """Parse LLM JSON response"""
        try:
            content = content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            return json.loads(content.strip())
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            return {}
