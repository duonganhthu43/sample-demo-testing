"""
Itinerary Agent for Travel Planning
Uses LLM to generate comprehensive day-by-day travel itineraries
"""

import json
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

from ..utils.config import get_config
from ..utils.schemas import get_response_format, ITINERARY_SCHEMA


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


ITINERARY_SYSTEM_PROMPT = """You are a travel itinerary planning expert. Create a detailed day-by-day itinerary based on the provided research data.

## CRITICAL: UNIQUENESS RULE (HIGHEST PRIORITY)

**Before generating the itinerary, mentally allocate unique items for each day:**
- For an N-day trip, you need N different breakfast spots, N different lunch restaurants, N different dinner restaurants
- Count the available restaurants and activities in the research data
- Assign EXACTLY ONE unique restaurant to each meal slot across all days
- Assign EXACTLY ONE unique activity/attraction to each time slot - never revisit

**VIOLATION CHECK**: If "Sushi Zanmai" appears on Day 1 dinner, it CANNOT appear on Day 2, Day 3, or any other day for ANY meal. Same for "Ichiran Ramen" or any other restaurant/attraction.

## Key Guidelines

1. **Use Research Data**: Use ONLY data from the provided research (activities, restaurants, flights, hotels)

2. **Realistic Scheduling**:
   - Allow travel time between locations
   - Breakfast: 7:00-9:00 AM | Lunch: 12:00-1:30 PM | Dinner: 6:30-8:00 PM (adjust for local culture)
   - Don't overschedule - include buffer time

3. **Detailed Descriptions** (see schema descriptions for format):
   - FLIGHTS: Airport arrival time, passport reminder, duration, transport from airport with costs
   - ATTRACTIONS: What to experience, opening hours, transport with costs
   - MEALS: Use restaurant data - name, dishes, price per person, reservation/wait info

4. **Cost Accuracy**:
   - Use actual prices from research data
   - Sum: flights + (hotel × nights) + activities + meals + transport

5. **Respect Constraints**: Stay within budget, honor hard constraints

The response schema has detailed descriptions for each field - follow those exactly.
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

        # Build structured content array for better LLM understanding
        user_content = self._build_itinerary_content(context)

        # Get LLM client
        client = self.config.get_llm_client(label="itinerary_agent")

        try:
            response = self._invoke_itinerary_llm(client, user_content)
            content = self._extract_llm_content(response)
            itinerary_data = self._parse_llm_response(content)
            normalized = self._normalize_itinerary_data(itinerary_data)

            # Fix duplicate meals by replacing with unused alternatives
            normalized = self._fix_duplicate_meals(normalized, context)

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

    def _build_itinerary_content(self, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Build structured content array for itinerary generation.

        Returns an array of content parts for better LLM understanding:
        - Separates trip details, research data, and constraints
        - Uses JSON for structured data
        """
        content_parts = []

        # Part 1: Trip details as JSON
        trip_details = {
            "destination": context.get("destination", "Unknown"),
            "travel_dates": context.get("travel_dates", "TBD"),
            "num_days": context.get("num_days", 5)
        }
        content_parts.append({
            "type": "text",
            "text": f"## Trip Details\n\n```json\n{json.dumps(trip_details, indent=2)}\n```"
        })

        # Part 2: Constraints as JSON
        constraints = context.get("constraints", {})
        if constraints:
            constraint_data = {
                "budget": constraints.get("budget", "Not specified"),
                "preferences": constraints.get("preferences", []),
                "hard_constraints": constraints.get("hard_constraints", [])
            }
            content_parts.append({
                "type": "text",
                "text": f"## Constraints\n\n```json\n{json.dumps(constraint_data, indent=2)}\n```"
            })

        # Part 3: Research data
        research = context.get("research", [])
        research_data = {}
        for item in research:
            item_type = item.get("type", "")

            if item_type == "destination":
                research_data["destination_info"] = {
                    "overview": item.get("overview", "")[:500],
                    "visa_requirements": item.get("visa_requirements", "Check requirements"),
                    "language": item.get("language", ""),
                    "currency": item.get("currency", ""),
                    "cultural_tips": item.get("cultural_tips", []),
                    "local_cuisine": item.get("local_cuisine", [])
                }

            elif item_type == "flights":
                research_data["flights"] = {
                    "best_outbound": item.get("best_outbound"),
                    "best_return": item.get("best_return"),
                    "outbound_options": item.get("outbound_options", [])[:3],
                    "return_options": item.get("return_options", [])[:3]
                }

            elif item_type == "accommodations":
                research_data["accommodations"] = self._strip_base64_from_data({
                    "best_value": item.get("best_value"),
                    "highest_rated": item.get("highest_rated"),
                    "options": item.get("hotels", [])[:5]
                })

            elif item_type == "activities":
                research_data["activities"] = self._strip_base64_from_data({
                    "activities": item.get("activities", []),
                    "must_do": item.get("must_do", []),
                    "free_activities": item.get("free_activities", [])
                })

            elif item_type == "restaurants":
                research_data["restaurants"] = self._strip_base64_from_data({
                    "breakfast_options": item.get("breakfast_options", [])[:5],
                    "lunch_options": item.get("lunch_options", [])[:8],
                    "dinner_options": item.get("dinner_options", [])[:8],
                    "budget_friendly": item.get("budget_friendly", [])[:5],
                    "by_area": item.get("by_area", {})
                })

        if research_data:
            content_parts.append({
                "type": "text",
                "text": f"## Research Data\n\n```json\n{json.dumps(research_data, indent=2, default=str)}\n```"
            })

        # Part 4: Weather data
        weather = context.get("weather", {})
        if weather:
            summary = weather.get("summary", {})
            weather_data = {
                "average_temp": summary.get("average_temp", "N/A"),
                "average_rain_chance": summary.get("average_rain_chance", 0),
                "packing_suggestions": weather.get("packing_suggestions", [])
            }
            content_parts.append({
                "type": "text",
                "text": f"## Weather\n\n```json\n{json.dumps(weather_data, indent=2)}\n```"
            })

        # Part 5: Cost analysis
        for item in context.get("analysis", []):
            if item.get("type") == "cost":
                cost_data = {
                    "breakdown": item.get("breakdown", {}),
                    "cost_saving_tips": item.get("cost_saving_tips", [])
                }
                content_parts.append({
                    "type": "text",
                    "text": f"## Cost Analysis\n\n```json\n{json.dumps(cost_data, indent=2, default=str)}\n```"
                })
                break

        # Part 6: Task instruction
        content_parts.append({
            "type": "text",
            "text": "## Task\n\nCreate a detailed day-by-day itinerary based on the research data above."
        })

        return content_parts

    def _invoke_itinerary_llm(self, client: Any, user_content: List[Dict[str, Any]]) -> Any:
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
                        "content": user_content  # Array of {"type": "text", "text": ...}
                    }
                ],
                response_format=get_response_format("itinerary", ITINERARY_SCHEMA),
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
                            "content": user_content  # Array of {"type": "text", "text": ...}
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

    def _fix_duplicate_meals(
        self,
        itinerary_data: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Post-process itinerary to ensure each restaurant only appears ONCE
        in the entire trip. Travelers want to explore different dining options!

        Uses fuzzy matching to handle variations like:
        - "Afuri Ramen" vs "Afuri Ramen - Ebisu"
        - "Sushi Zanmai" vs "Sushi Zanmai (famous for fresh fish)"
        """
        import re

        # Get available restaurants from context - check multiple possible keys
        available_restaurants: List[Dict[str, Any]] = []
        for item in context.get("research", []):
            if item.get("type") == "restaurants":
                # Try "restaurants" key first, then combine from meal options
                available_restaurants = item.get("restaurants", [])
                if not available_restaurants:
                    # Fallback: combine from breakfast/lunch/dinner options
                    available_restaurants = []
                    available_restaurants.extend(item.get("breakfast_options", []))
                    available_restaurants.extend(item.get("lunch_options", []))
                    available_restaurants.extend(item.get("dinner_options", []))
                break

        if not available_restaurants:
            print("  Warning: No restaurant data found for duplicate fix")
            return itinerary_data

        # Map of normalized name -> full restaurant data
        # Key is lowercase with extra whitespace removed
        restaurant_map: Dict[str, Dict[str, Any]] = {}
        restaurant_names_lower: List[str] = []  # For fuzzy matching
        for r in available_restaurants:
            name = r.get("name", "")
            if name:
                normalized = " ".join(name.lower().split())  # Normalize whitespace
                restaurant_map[normalized] = r
                restaurant_names_lower.append(normalized)

        def find_canonical_restaurant(location: str) -> Optional[str]:
            """
            Find the canonical restaurant name from research data that matches
            the location string extracted from the itinerary.

            Handles variations like:
            - Exact match: "afuri ramen" matches "afuri ramen"
            - Prefix match: "afuri ramen - ebisu" matches "afuri ramen"
            - Contains match: "dinner at afuri ramen famous for yuzu" matches "afuri ramen"
            """
            location = " ".join(location.lower().split())  # Normalize whitespace

            # 1. Exact match
            if location in restaurant_map:
                return location

            # 2. Check if any known restaurant name is a prefix of the location
            for name in restaurant_names_lower:
                if location.startswith(name):
                    return name

            # 3. Check if any known restaurant name is contained in the location
            for name in restaurant_names_lower:
                if name in location:
                    return name

            # 4. Check if location is contained in any known restaurant name
            for name in restaurant_names_lower:
                if location in name:
                    return name

            return None

        # Track restaurants used GLOBALLY by canonical name
        used_restaurants: set = set()  # canonical restaurant names (lowercase)
        meal_entries: List[tuple] = []  # (day_idx, item_idx, meal_type, canonical_name or None, original_activity)

        # First pass: identify all meal activities and their canonical restaurant names
        days = itinerary_data.get("days", [])
        for day_idx, day in enumerate(days):
            schedule = day.get("schedule", [])

            for item_idx, item in enumerate(schedule):
                activity = item.get("activity", "")
                activity_lower = activity.lower()

                # Check if this is a meal activity
                for meal_type in ["breakfast", "lunch", "dinner"]:
                    if activity_lower.startswith(meal_type):
                        # Extract location after "at "
                        match = re.search(rf'{meal_type}\s+at\s+(.+)', activity_lower)
                        if match:
                            location = match.group(1).strip()
                            canonical = find_canonical_restaurant(location)
                            meal_entries.append((day_idx, item_idx, meal_type, canonical, activity))
                        break

        # Second pass: identify duplicates and fix them
        duplicates_fixed = 0

        # Track all restaurant strings we've seen (for unknown restaurants)
        all_seen_locations: set = set()

        for day_idx, item_idx, meal_type, canonical, original_activity in meal_entries:
            # Extract location for unknown restaurant tracking
            activity_lower = original_activity.lower()
            match = re.search(rf'{meal_type}\s+at\s+(.+)', activity_lower)
            raw_location = match.group(1).strip() if match else ""

            # If unknown restaurant, check for raw location duplicates
            if canonical is None:
                if raw_location and raw_location in all_seen_locations:
                    # This unknown restaurant was already used - replace with generic
                    item = days[day_idx]["schedule"][item_idx]
                    day_num = days[day_idx].get("day", day_idx + 1)
                    item["activity"] = f"{meal_type.capitalize()} - Local restaurant near Day {day_num} area"
                    # Clear old image suggestion so presentation layer regenerates it
                    item.pop("image_suggestion", None)
                    item.pop("image_placeholder", None)
                    print(f"    Replaced unknown duplicate '{raw_location}' with generic")
                    duplicates_fixed += 1
                else:
                    all_seen_locations.add(raw_location)
                continue

            # Track the canonical name as seen
            all_seen_locations.add(canonical)

            if canonical in used_restaurants:
                # This restaurant was already used - need to replace
                # Find an unused restaurant
                replacement = None
                for name, data in restaurant_map.items():
                    if name not in used_restaurants:
                        replacement = data
                        used_restaurants.add(name)
                        break

                item = days[day_idx]["schedule"][item_idx]
                if replacement:
                    new_activity = f"{meal_type.capitalize()} at {replacement['name']}"
                    item["activity"] = new_activity
                    # Clear old image suggestion so presentation layer regenerates it
                    item.pop("image_suggestion", None)
                    item.pop("image_placeholder", None)
                    if replacement.get("cuisine_type"):
                        old_notes = item.get("notes", "")
                        item["notes"] = f"{replacement['cuisine_type']} cuisine. {old_notes}".strip()
                    print(f"    Replaced duplicate '{canonical}' with '{replacement['name']}'")
                else:
                    # No unused restaurant available - use a generic description
                    day_num = days[day_idx].get("day", day_idx + 1)
                    item["activity"] = f"{meal_type.capitalize()} - Local restaurant near Day {day_num} area"
                    # Clear old image suggestion
                    item.pop("image_suggestion", None)
                    item.pop("image_placeholder", None)
                    print(f"    Replaced duplicate '{canonical}' with generic (no alternatives)")
                duplicates_fixed += 1
            else:
                # First occurrence - mark as used
                used_restaurants.add(canonical)

        if duplicates_fixed > 0:
            print(f"  Fixed {duplicates_fixed} duplicate restaurant entries.")
        else:
            print(f"  No duplicate restaurants found (checked {len(meal_entries)} meals)")

        return itinerary_data

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
