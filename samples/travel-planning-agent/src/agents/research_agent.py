"""
Research Agent for Travel Planning
Gathers information about destinations, flights, hotels, and activities using Tavily + LLM
"""

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

from ..utils.config import get_config
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


DESTINATION_EXTRACTION_PROMPT = """You are a travel information extraction expert. Your task is to extract structured travel information from raw search results.

## Input
You will receive a JSON object with:
- "destination": The travel destination name
- "search_results": Array of search result text content

Extract the following information:

## Output Format
Return a valid JSON object with this structure:
```json
{
    "overview": "2-3 sentence overview of the destination",
    "visa_requirements": "Visa requirements for tourists (be specific about duration, requirements)",
    "best_time_to_visit": "Best months/seasons to visit with reasoning",
    "language": "Official language(s) and English proficiency level",
    "currency": "Local currency name and code (e.g., 'Japanese Yen (JPY)')",
    "time_zone": "Timezone abbreviation and UTC offset (e.g., 'JST (UTC+9)')",
    "cultural_tips": ["Tip 1", "Tip 2", "Tip 3", "Tip 4"],
    "safety_rating": "Very Safe / Safe / Moderate / Exercise Caution",
    "local_cuisine": ["Dish 1", "Dish 2", "Dish 3"]
}
```

## Guidelines:
1. Extract ONLY information found in the search results
2. If information is not found, provide a reasonable general answer based on the destination
3. Be specific and actionable in your tips
4. Cultural tips should be practical for tourists
5. Local cuisine should list specific dishes, not general descriptions
6. Safety rating should be based on search results or general knowledge

IMPORTANT: Return ONLY the JSON object, no markdown formatting or explanation."""


class ResearchAgent:
    """
    Research agent for gathering travel information using Tavily + LLM
    """

    def __init__(self, config=None):
        self.config = config or get_config()
        self.mock_mode = self.config.app.mock_external_apis
        self.flight_tool = FlightSearchTool()
        self.hotel_tool = HotelSearchTool()
        self.activity_tool = ActivitySearchTool()

        if self.config.search.tavily_api_key:
            print("ResearchAgent initialized with Tavily API")
        else:
            if self.mock_mode:
                print("Warning: Tavily API key not found - will use fallback data")
            else:
                raise ValueError("TAVILY_API_KEY is required when MOCK_EXTERNAL_APIS=false")

    def research_destination(self, destination: str) -> DestinationResult:
        """
        Research destination information using Tavily + LLM

        Args:
            destination: Name of destination city/country

        Returns:
            DestinationResult with comprehensive destination info
        """
        print(f"Researching destination: {destination} via Tavily + LLM...")

        # Always try Tavily first - fallback is handled inside
        return self._search_tavily_destination(destination)

    def _search_tavily_destination(self, destination: str) -> DestinationResult:
        """Search for destination info using Tavily API and extract with LLM"""
        try:
            from tavily import TavilyClient

            client = TavilyClient(api_key=self.config.search.tavily_api_key)

            # Collect all search results
            all_content = []
            sources = []

            queries = [
                f"{destination} travel guide overview",
                f"{destination} visa requirements tourists",
                f"{destination} best time to visit weather",
                f"{destination} local language currency timezone",
                f"{destination} cultural etiquette customs tips",
                f"{destination} local food cuisine must try dishes",
                f"{destination} safety travel advisory",
            ]

            def execute_query(query: str) -> dict:
                """Execute a single Tavily query"""
                try:
                    print(f"  Tavily query: {query}")
                    return client.search(
                        query=query,
                        max_results=3,
                        search_depth="basic"
                    )
                except Exception as e:
                    print(f"  Query failed: {str(e)}")
                    return {"results": []}

            # Execute all queries in parallel using ThreadPoolExecutor
            print(f"  Executing {len(queries)} Tavily queries in parallel...")
            with ThreadPoolExecutor(max_workers=len(queries)) as executor:
                futures = {executor.submit(execute_query, q): q for q in queries}
                for future in as_completed(futures):
                    response = future.result()
                    for result in response.get("results", []):
                        content = result.get("content", "")
                        url = result.get("url", "")
                        if content:
                            all_content.append(content)
                        if url and url not in sources:
                            sources.append(url)

            # Use LLM to extract structured info from all content
            if all_content:
                print(f"  Tavily returned {len(all_content)} content items, extracting with LLM...")
                extracted = self._extract_with_llm(destination, all_content)
            else:
                print("  No content from Tavily, using default values")
                extracted = {}

            return DestinationResult(
                destination=destination,
                overview=extracted.get("overview", f"{destination} is a popular tourist destination."),
                visa_requirements=extracted.get("visa_requirements", "Check with your local embassy for visa requirements."),
                best_time_to_visit=extracted.get("best_time_to_visit", "Research local weather patterns for the best time to visit."),
                language=extracted.get("language", "Local language (English may be spoken in tourist areas)"),
                currency=extracted.get("currency", "Check local currency before traveling"),
                time_zone=extracted.get("time_zone", "Check local timezone"),
                cultural_tips=extracted.get("cultural_tips", ["Research local customs before visiting"]),
                safety_rating=extracted.get("safety_rating", "Check travel advisories"),
                local_cuisine=extracted.get("local_cuisine", []),
                sources=sources[:5]
            )

        except Exception as e:
            print(f"Tavily destination search failed: {str(e)}")
            if self.mock_mode:
                return self._generate_fallback_destination(destination)
            raise

    def _extract_with_llm(self, destination: str, content_list: List[str]) -> Dict[str, Any]:
        """Use LLM to extract structured info from search results"""
        try:
            # Get LLM client
            llm_client = self.config.get_llm_client(label="research_extraction")

            # Prepare structured input (limit to avoid token limits)
            truncated_content = []
            total_chars = 0
            for content in content_list[:10]:
                if total_chars + len(content) > 8000:
                    break
                truncated_content.append(content)
                total_chars += len(content)

            # Structure the input as JSON for cleaner separation of data and instructions
            user_input = {
                "destination": destination,
                "search_results": truncated_content
            }

            try:
                response = llm_client.chat.completions.create(
                    model=self.config.llm.model,
                    messages=[
                        {
                            "role": "system",
                            "content": DESTINATION_EXTRACTION_PROMPT
                        },
                        {
                            "role": "user",
                            "content": json.dumps(user_input)
                        }
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.2,
                    max_tokens=1500
                )
            except Exception as e:
                msg = str(e).lower()
                if "response_format" in msg or "unknown" in msg or "unsupported" in msg:
                    response = llm_client.chat.completions.create(
                        model=self.config.llm.model,
                        messages=[
                            {
                                "role": "system",
                                "content": DESTINATION_EXTRACTION_PROMPT
                            },
                            {
                                "role": "user",
                                "content": json.dumps(user_input)
                            }
                        ],
                        temperature=0.2,
                        max_tokens=1500
                    )
                else:
                    raise

            content = response.choices[0].message.content
            return self._parse_llm_response(content)

        except Exception as e:
            print(f"LLM extraction failed: {str(e)}")
            return {}

    def _parse_llm_response(self, content: str) -> Dict[str, Any]:
        """Parse LLM JSON response"""
        try:
            content = content.strip()

            # Remove markdown code blocks if present
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

    def _generate_fallback_destination(self, destination: str) -> DestinationResult:
        """Generate fallback destination info using LLM only"""
        try:
            # Try to use LLM with general knowledge
            llm_client = self.config.get_llm_client(label="research_agent_fallback")

            response = llm_client.chat.completions.create(
                model=self.config.llm.model,
                messages=[
                    {
                        "role": "system",
                        "content": DESTINATION_EXTRACTION_PROMPT
                    },
                    {
                        "role": "user",
                        "content": f"Based on your knowledge, provide travel information for {destination}. Include visa requirements, language, currency, timezone, cultural tips, safety rating, and local cuisine."
                    }
                ],
                temperature=0.3,
                max_tokens=1500
            )

            content = response.choices[0].message.content
            extracted = self._parse_llm_response(content)

            return DestinationResult(
                destination=destination,
                overview=extracted.get("overview", f"{destination} is a popular tourist destination."),
                visa_requirements=extracted.get("visa_requirements", "Check with your local embassy for visa requirements."),
                best_time_to_visit=extracted.get("best_time_to_visit", "Research local weather patterns for best timing."),
                language=extracted.get("language", "Local language (research before visiting)"),
                currency=extracted.get("currency", "Check local currency before traveling"),
                time_zone=extracted.get("time_zone", "Check local timezone"),
                cultural_tips=extracted.get("cultural_tips", ["Research local customs before visiting"]),
                safety_rating=extracted.get("safety_rating", "Check travel advisories"),
                local_cuisine=extracted.get("local_cuisine", []),
                sources=[]
            )

        except Exception as e:
            print(f"Fallback LLM generation failed: {str(e)}")
            # Ultimate fallback - minimal info
            return DestinationResult(
                destination=destination,
                overview=f"{destination} is a travel destination. Please research specific details.",
                visa_requirements="Check with your local embassy for visa requirements.",
                best_time_to_visit="Research local weather patterns.",
                language="Research local language.",
                currency="Research local currency.",
                time_zone="Research local timezone.",
                cultural_tips=["Research local customs before visiting"],
                safety_rating="Check travel advisories",
                local_cuisine=[],
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
