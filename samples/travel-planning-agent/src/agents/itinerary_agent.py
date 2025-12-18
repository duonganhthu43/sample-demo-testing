"""
Itinerary Agent for Travel Planning
Uses LLM to generate comprehensive day-by-day travel itineraries
"""

import json
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

from ..utils.config import get_config


@dataclass
class ItineraryResult:
    """Result from itinerary generation"""
    destination: str
    travel_dates: str
    days: List[Dict[str, Any]]
    total_estimated_cost: float
    currency: str
    summary: str
    packing_list: List[str]
    important_notes: List[str]
    flights: Optional[Dict[str, Any]] = None
    accommodation: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "destination": self.destination,
            "travel_dates": self.travel_dates,
            "flights": self.flights,
            "accommodation": self.accommodation,
            "days": self.days,
            "total_estimated_cost": self.total_estimated_cost,
            "currency": self.currency,
            "summary": self.summary,
            "packing_list": self.packing_list,
            "important_notes": self.important_notes
        }


@dataclass
class SummaryResult:
    """Result from summary generation"""
    trip_overview: str
    highlights: List[str]
    budget_summary: Dict[str, Any]
    key_bookings: List[Dict[str, Any]]
    preparation_checklist: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "trip_overview": self.trip_overview,
            "highlights": self.highlights,
            "budget_summary": self.budget_summary,
            "key_bookings": self.key_bookings,
            "preparation_checklist": self.preparation_checklist
        }


ITINERARY_SYSTEM_PROMPT = """You are a travel itinerary planning expert. Your task is to create a detailed day-by-day itinerary based on the provided research data.

## Your Output
Return a valid JSON object with this exact structure:
```json
{
    "days": [
        {
            "day": 1,
            "date": "Day 1",
            "theme": "Arrival & First Impressions",
            "schedule": [
                {
                    "time": "09:00 - 11:00",
                    "activity": "Activity name",
                    "location": "Location name",
                    "category": "Category",
                    "notes": "Helpful tips",
                    "cost": 25.00,
                    "source_url": "optional url"
                }
            ],
            "day_cost": 100.00
        }
    ],
    "total_estimated_cost": 1500.00,
    "summary": "Brief trip summary",
    "packing_list": ["item1", "item2"],
    "important_notes": ["note1", "note2"]
}
```

## Guidelines
1. **Timing**: Create realistic schedules with appropriate time for each activity
   - Consider travel time between locations
   - Include meal breaks at appropriate local times
   - Don't overschedule - allow buffer time

2. **Activities**: Use ONLY activities from the provided research data
   - Include the actual prices from the data
   - Use source URLs if available
   - Categorize appropriately

3. **Meals**: Include breakfast, lunch, and dinner
   - Use food activities from research if available
   - Estimate meal costs based on the destination's cost level
   - Suggest local cuisine mentioned in destination info

4. **Cost Calculation**: Be accurate
   - Sum actual flight costs from flight data
   - Calculate hotel costs (price_per_night × nights)
   - Sum activity costs
   - Estimate daily food and transport based on destination

5. **Constraints**: Respect user constraints
   - Stay within budget
   - Honor max activities per day preference
   - Meet hard constraints (arrival times, direct flights, etc.)

6. **Packing List**: Based on weather and destination
   - Include weather-appropriate clothing
   - Add destination-specific items (temple visits = modest clothing)
   - Include practical essentials

7. **Important Notes**: Include actionable information
   - Visa requirements
   - Weather warnings
   - Cultural tips
   - Hard constraints reminders

IMPORTANT: Return ONLY the JSON object, no markdown formatting or explanation.
"""


class ItineraryAgent:
    """
    Agent for generating travel itineraries using LLM
    """

    def __init__(self, config=None):
        self.config = config or get_config()

    def generate_itinerary(
        self,
        context: Dict[str, Any]
    ) -> ItineraryResult:
        """
        Generate a comprehensive itinerary using LLM

        Args:
            context: All gathered research and analysis results

        Returns:
            ItineraryResult with day-by-day plan
        """
        print("Generating comprehensive itinerary with LLM...")

        # Prepare context summary for LLM
        context_summary = self._prepare_context_summary(context)

        # Get LLM client
        client = self.config.get_llm_client(label="itinerary_agent")

        try:
            response = self._invoke_itinerary_llm(client, context_summary)
            content = self._extract_llm_content(response)
            itinerary_data = self._parse_llm_response(content)
            normalized = self._normalize_itinerary_data(itinerary_data)

            # Extract flight and hotel info for output
            flights = self._extract_flights(context)
            hotels = self._extract_hotels(context)

            print(
                f"Itinerary JSON validated ({len(normalized['days'])} days, "
                f"estimated cost ≈ ${normalized['total_estimated_cost']:.2f})."
            )

            return ItineraryResult(
                destination=context.get("destination", "Unknown"),
                travel_dates=context.get("travel_dates", ""),
                days=normalized.get("days", []),
                total_estimated_cost=normalized.get("total_estimated_cost", 0.0),
                currency="USD",
                summary=normalized.get("summary", ""),
                packing_list=normalized.get("packing_list", []),
                important_notes=normalized.get("important_notes", []),
                flights=flights,
                accommodation=hotels
            )

        except Exception as e:
            print(f"LLM itinerary generation failed: {str(e)}")
            # Fallback to basic generation
            return self._fallback_generate(context)

    def _prepare_context_summary(self, context: Dict[str, Any]) -> str:
        """Prepare a structured summary of context for LLM"""
        sections = []

        # Basic trip info
        sections.append("## TRIP DETAILS")
        sections.append(f"Destination: {context.get('destination', 'Unknown')}")
        sections.append(f"Travel Dates: {context.get('travel_dates', 'TBD')}")
        sections.append(f"Number of Days: {context.get('num_days', 5)}")

        # Constraints
        constraints = context.get("constraints", {})
        if constraints:
            sections.append("\n## CONSTRAINTS")
            sections.append(f"Budget: {constraints.get('budget', 'Not specified')}")
            sections.append(f"Preferences: {constraints.get('preferences', [])}")
            sections.append(f"Hard Constraints: {constraints.get('hard_constraints', [])}")

        # Research data
        research = context.get("research", [])
        for item in research:
            item_type = item.get("type", "")

            if item_type == "destination":
                sections.append("\n## DESTINATION INFO")
                sections.append(f"Overview: {item.get('overview', '')[:300]}")
                sections.append(f"Visa: {item.get('visa_requirements', 'Check requirements')}")
                sections.append(f"Language: {item.get('language', '')}")
                sections.append(f"Currency: {item.get('currency', '')}")
                sections.append(f"Culture Tips: {item.get('cultural_tips', [])}")
                sections.append(f"Local Cuisine: {item.get('local_cuisine', [])}")

            elif item_type == "flights":
                sections.append("\n## FLIGHT DATA")
                sections.append(json.dumps({
                    "best_outbound": item.get("best_outbound"),
                    "best_return": item.get("best_return"),
                    "outbound_options": item.get("outbound_options", [])[:3],
                    "return_options": item.get("return_options", [])[:3]
                }, indent=2, default=str))

            elif item_type == "accommodations":
                sections.append("\n## ACCOMMODATION DATA")
                sections.append(json.dumps(self._strip_base64_from_data({
                    "best_value": item.get("best_value"),
                    "highest_rated": item.get("highest_rated"),
                    "options": item.get("hotels", [])[:5]
                }), indent=2, default=str))

            elif item_type == "activities":
                sections.append("\n## ACTIVITIES DATA")
                sections.append(json.dumps(self._strip_base64_from_data({
                    "activities": item.get("activities", []),
                    "must_do": item.get("must_do", []),
                    "free_activities": item.get("free_activities", [])
                }), indent=2, default=str))

        # Weather
        weather = context.get("weather", {})
        if weather:
            sections.append("\n## WEATHER")
            summary = weather.get("summary", {})
            sections.append(f"Average Temp: {summary.get('average_temp', 'N/A')}°C")
            sections.append(f"Rain Chance: {summary.get('average_rain_chance', 0)}%")
            sections.append(f"Packing Suggestions: {weather.get('packing_suggestions', [])}")

        # Cost analysis
        for item in context.get("analysis", []):
            if item.get("type") == "cost":
                sections.append("\n## COST ANALYSIS")
                sections.append(f"Breakdown: {item.get('breakdown', {})}")
                sections.append(f"Tips: {item.get('cost_saving_tips', [])}")

        return "\n".join(sections)

    def _invoke_itinerary_llm(self, client: Any, context_summary: str) -> Any:
        try:
            return client.chat.completions.create(
                model=self.config.llm.model,
                messages=[
                    {
                        "role": "system",
                        "content": ITINERARY_SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": (
                            "Create a detailed day-by-day itinerary based on this "
                            f"research data:\n\n{context_summary}"
                        )
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
                max_tokens=4000
            )
        except Exception as e:
            msg = str(e).lower()
            if "response_format" in msg or "unknown" in msg or "unsupported" in msg:
                print("Retrying itinerary generation without JSON enforcement (gateway limitation).")
                return client.chat.completions.create(
                    model=self.config.llm.model,
                    messages=[
                        {
                            "role": "system",
                            "content": ITINERARY_SYSTEM_PROMPT
                        },
                        {
                            "role": "user",
                            "content": (
                                "Create a detailed day-by-day itinerary based on this "
                                f"research data:\n\n{context_summary}"
                            )
                        }
                    ],
                    temperature=0.3,
                    max_tokens=4000
                )
            raise

    def _extract_llm_content(self, response: Any) -> str:
        choices = getattr(response, "choices", None)
        if not choices:
            raise ValueError("Itinerary LLM response contained no choices")

        first_choice = choices[0]
        message = getattr(first_choice, "message", None) if first_choice else None
        content = getattr(message, "content", None) if message else None

        if not content:
            raise ValueError("Itinerary LLM response was empty")

        print(f"Received itinerary response ({len(content)} chars).")
        return content

    def _normalize_itinerary_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(data, dict):
            raise ValueError("Itinerary data must be a JSON object")

        normalized: Dict[str, Any] = dict(data)

        days = normalized.get("days")
        if not isinstance(days, list) or not days:
            raise ValueError("Itinerary data must include a non-empty days list")

        cleaned_days: List[Dict[str, Any]] = []
        for idx, day in enumerate(days):
            if not isinstance(day, dict):
                raise ValueError(f"Day {idx + 1} must be an object")
            schedule = day.get("schedule", [])
            if not isinstance(schedule, list):
                raise ValueError(f"Day {idx + 1} schedule must be a list")
            cleaned_schedule = [item for item in schedule if isinstance(item, dict)]
            cleaned_day = dict(day)
            cleaned_day["schedule"] = cleaned_schedule
            cleaned_days.append(cleaned_day)
        normalized["days"] = cleaned_days

        total_cost = normalized.get("total_estimated_cost")
        if total_cost is None:
            raise ValueError("Itinerary data missing total_estimated_cost")
        try:
            normalized["total_estimated_cost"] = float(total_cost)
        except (TypeError, ValueError):
            raise ValueError("total_estimated_cost must be numeric")

        for key in ("packing_list", "important_notes"):
            value = normalized.get(key, [])
            if isinstance(value, list):
                normalized[key] = value
            elif isinstance(value, str):
                normalized[key] = [value]
            elif value is None:
                normalized[key] = []
            else:
                raise ValueError(f"{key} must be a list or string")

        summary = normalized.get("summary")
        if summary is None:
            normalized["summary"] = ""
        elif not isinstance(summary, str):
            raise ValueError("summary must be a string")

        return normalized

    def _strip_base64_from_data(self, data: Any) -> Any:
        if isinstance(data, dict):
            result: Dict[str, Any] = {}
            for key, value in data.items():
                if key == "image_base64":
                    if value:
                        result["has_image"] = True
                    continue
                result[key] = self._strip_base64_from_data(value)
            return result

        if isinstance(data, list):
            if len(data) > 50:
                data = data[:50]
            return [self._strip_base64_from_data(item) for item in data]

        if isinstance(data, str):
            if len(data) > 2000:
                return data[:2000] + "..."
            return data

        return data

    def _parse_llm_response(self, content: str) -> Dict[str, Any]:
        """Parse LLM JSON response"""
        try:
            # Try to extract JSON from response
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
            raise ValueError(f"Invalid JSON from itinerary LLM: {e}") from e

    def _extract_flights(self, context: Dict) -> Optional[Dict[str, Any]]:
        """Extract and format flight data from context"""
        for item in context.get("research", []):
            if item.get("type") == "flights":
                result = {
                    "outbound": None,
                    "return": None,
                    "total_flight_cost": 0,
                    "all_outbound_options": item.get("outbound_options", [])[:5],
                    "all_return_options": item.get("return_options", [])[:5]
                }

                best_out = item.get("best_outbound")
                if best_out:
                    result["outbound"] = best_out
                    result["total_flight_cost"] += best_out.get("price", 0)
                elif item.get("outbound_options"):
                    result["outbound"] = item["outbound_options"][0]
                    result["total_flight_cost"] += item["outbound_options"][0].get("price", 0)

                best_ret = item.get("best_return")
                if best_ret:
                    result["return"] = best_ret
                    result["total_flight_cost"] += best_ret.get("price", 0)
                elif item.get("return_options"):
                    result["return"] = item["return_options"][0]
                    result["total_flight_cost"] += item["return_options"][0].get("price", 0)

                return result
        return None

    def _extract_hotels(self, context: Dict) -> Optional[Dict[str, Any]]:
        """Extract and format hotel data from context"""
        for item in context.get("research", []):
            if item.get("type") == "accommodations":
                best = item.get("best_value") or item.get("highest_rated")
                return {
                    "recommended": best,
                    "all_options": item.get("hotels", [])[:8],
                    "total_options": item.get("total_options", 0),
                    "filters_applied": item.get("filters_applied", {})
                }
        return None

    def _fallback_generate(self, context: Dict[str, Any]) -> ItineraryResult:
        """Fallback itinerary generation if LLM fails"""
        destination = context.get("destination", "Unknown")
        num_days = context.get("num_days", 5)

        # Get activities
        activities = []
        for item in context.get("research", []):
            if item.get("type") == "activities":
                activities = item.get("activities", [])

        # Simple day generation
        days = []
        act_idx = 0
        for day_num in range(1, num_days + 1):
            day = {
                "day": day_num,
                "date": f"Day {day_num}",
                "theme": f"Day {day_num} in {destination}",
                "schedule": [],
                "day_cost": 0
            }

            # Add activities
            for _ in range(2):
                if act_idx < len(activities):
                    act = activities[act_idx]
                    day["schedule"].append({
                        "time": "See activity details",
                        "activity": act.get("name", "Activity"),
                        "location": act.get("location", destination),
                        "category": act.get("category", "Sightseeing"),
                        "notes": "",
                        "cost": act.get("price", 0)
                    })
                    day["day_cost"] += act.get("price", 0)
                    act_idx += 1

            days.append(day)

        return ItineraryResult(
            destination=destination,
            travel_dates=context.get("travel_dates", ""),
            days=days,
            total_estimated_cost=sum(d.get("day_cost", 0) for d in days),
            currency="USD",
            summary=f"{num_days}-day trip to {destination}",
            packing_list=["Passport", "Comfortable shoes", "Phone charger"],
            important_notes=["Check visa requirements", "Book accommodations in advance"],
            flights=self._extract_flights(context),
            accommodation=self._extract_hotels(context)
        )

    def generate_summary(
        self,
        itinerary: Dict[str, Any],
        context: Dict[str, Any]
    ) -> SummaryResult:
        """
        Generate an executive summary of the trip

        Args:
            itinerary: Generated itinerary
            context: All context data

        Returns:
            SummaryResult with trip summary
        """
        print("Generating trip summary...")

        destination = itinerary.get("destination", "Unknown")
        days = itinerary.get("days", [])
        total_cost = itinerary.get("total_estimated_cost", 0)

        # Extract highlights from activities
        highlights = []
        for day in days:
            for item in day.get("schedule", []):
                if item.get("category") not in ["Food", "Meal"]:
                    highlights.append(f"Day {day['day']}: {item['activity']}")

        # Get cost breakdown from analysis
        cost_breakdown = {}
        for item in context.get("analysis", []):
            if item.get("type") == "cost" and item.get("breakdown"):
                cost_breakdown = item.get("breakdown")
                break

        # Budget summary
        budget_summary = {
            "total_estimated": total_cost,
            "currency": "USD",
            "breakdown": cost_breakdown
        }

        # Key bookings from research
        bookings = []
        for item in context.get("research", []):
            if item.get("type") == "flights":
                best = item.get("best_outbound", {})
                if best:
                    bookings.append({
                        "type": "Flight",
                        "details": f"{best.get('airline', 'TBD')} - ${best.get('price', 'TBD')}",
                        "status": "Book in advance",
                        "priority": "High"
                    })
            if item.get("type") == "accommodations":
                best = item.get("best_value") or item.get("highest_rated", {})
                if best:
                    bookings.append({
                        "type": "Hotel",
                        "details": f"{best.get('name', 'TBD')} - ${best.get('price_per_night', 'TBD')}/night",
                        "status": "Book in advance",
                        "priority": "High"
                    })

        # Checklist from destination info
        checklist = ["Check passport validity"]
        for item in context.get("research", []):
            if item.get("type") == "destination":
                visa = item.get("visa_requirements", "")
                if visa:
                    checklist.append(f"Visa: {visa}")
                break

        checklist.extend([
            "Book flights",
            "Book accommodation",
            "Get travel insurance",
            "Notify bank of travel dates"
        ])

        return SummaryResult(
            trip_overview=f"A {len(days)}-day adventure to {destination}",
            highlights=highlights[:5],
            budget_summary=budget_summary,
            key_bookings=bookings,
            preparation_checklist=checklist
        )
