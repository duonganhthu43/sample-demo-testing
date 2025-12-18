"""
Analysis Agent for Travel Planning
Uses LLM to analyze itinerary feasibility, costs, and schedule optimization
"""

import json
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional

from ..utils.config import get_config
from ..utils.schemas import (
    get_response_format,
    FEASIBILITY_ANALYSIS_SCHEMA,
    COST_BREAKDOWN_SCHEMA,
    SCHEDULE_OPTIMIZATION_SCHEMA
)


@dataclass
class FeasibilityResult:
    """Result from feasibility analysis"""
    is_feasible: bool
    confidence: float
    issues: List[str]
    warnings: List[str]
    suggestions: List[str]
    schedule_analysis: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_feasible": self.is_feasible,
            "confidence": self.confidence,
            "issues": self.issues,
            "warnings": self.warnings,
            "suggestions": self.suggestions,
            "schedule_analysis": self.schedule_analysis
        }


@dataclass
class CostBreakdownResult:
    """Result from cost analysis"""
    total_estimated_cost: float
    currency: str
    breakdown: Dict[str, float]
    within_budget: bool
    budget_remaining: float
    cost_saving_tips: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_estimated_cost": self.total_estimated_cost,
            "currency": self.currency,
            "breakdown": self.breakdown,
            "within_budget": self.within_budget,
            "budget_remaining": self.budget_remaining,
            "cost_saving_tips": self.cost_saving_tips
        }


@dataclass
class ScheduleOptimizationResult:
    """Result from schedule optimization"""
    optimized_schedule: List[Dict[str, Any]]
    changes_made: List[str]
    time_saved: str
    efficiency_score: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "optimized_schedule": self.optimized_schedule,
            "changes_made": self.changes_made,
            "time_saved": self.time_saved,
            "efficiency_score": self.efficiency_score
        }


FEASIBILITY_SYSTEM_PROMPT = """You are a travel planning analyst specializing in itinerary feasibility assessment.

Analyze the provided itinerary and constraints to determine if the travel plan is realistic and achievable.

## Your Analysis Should Consider:
1. **Time Constraints**: Are there enough hours in each day for planned activities?
2. **Travel Logistics**: Can the traveler realistically move between locations?
3. **Budget Alignment**: Do costs align with the stated budget?
4. **Hard Constraints**: Are non-negotiable requirements (arrival times, direct flights) met?
5. **Preference Alignment**: Does the plan match stated preferences?
6. **Physical Feasibility**: Is the pace sustainable without exhaustion?

## Output Format
Return a valid JSON object:
```json
{
    "is_feasible": true,
    "confidence": 0.85,
    "issues": ["Critical problem that makes plan unfeasible"],
    "warnings": ["Potential concern to be aware of"],
    "suggestions": ["Recommendation to improve the plan"],
    "schedule_analysis": {
        "total_days": 5,
        "activities_per_day": 2,
        "estimated_daily_travel_time": "2.5 hours",
        "pace_assessment": "moderate",
        "buffer_time": "adequate"
    }
}
```

## Guidelines:
- `is_feasible`: true if plan can reasonably be executed, false if critical blockers exist
- `confidence`: 0.0-1.0 score based on how certain you are of the assessment
- `issues`: Only list genuine blockers that prevent execution
- `warnings`: List concerns that need attention but aren't blockers
- `suggestions`: Actionable improvements to make the plan better

IMPORTANT: Return ONLY the JSON object, no markdown formatting or explanation."""


COST_ANALYSIS_SYSTEM_PROMPT = """You are a travel budget analyst specializing in trip cost estimation.

Analyze the provided travel data to create an accurate cost breakdown and budget assessment.

## Your Analysis Should Include:
1. **Flights**: Extract actual prices from flight data
2. **Accommodation**: Calculate total hotel costs (price × nights)
3. **Activities**: Sum activity costs from provided data
4. **Food Estimate**: Based on destination's cost of living
5. **Local Transport**: Based on destination's transport costs
6. **Miscellaneous**: Buffer for unexpected expenses

## Output Format
Return a valid JSON object:
```json
{
    "total_estimated_cost": 1250.00,
    "currency": "USD",
    "breakdown": {
        "flights": 450.00,
        "accommodation": 400.00,
        "activities": 150.00,
        "food": 175.00,
        "local_transport": 50.00,
        "miscellaneous": 25.00
    },
    "within_budget": true,
    "budget_remaining": 250.00,
    "cost_saving_tips": [
        "Specific actionable tip based on the breakdown",
        "Another tip relevant to this destination"
    ]
}
```

## Guidelines:
- Use ACTUAL prices from the provided flight and hotel data
- Estimate food costs based on destination (expensive cities like Tokyo/London vs budget destinations)
- Estimate transport based on typical transit pass costs for the destination
- Provide destination-specific cost saving tips
- Be realistic but not pessimistic with estimates

IMPORTANT: Return ONLY the JSON object, no markdown formatting or explanation."""


SCHEDULE_OPTIMIZATION_SYSTEM_PROMPT = """You are a travel schedule optimizer specializing in efficient itinerary planning.

Optimize the provided activities into an efficient daily schedule that maximizes enjoyment while minimizing wasted time.

## Optimization Criteria:
1. **Geographic Grouping**: Activities in same area on same day
2. **Time Efficiency**: Minimize travel between locations
3. **Energy Management**: Mix high-energy and relaxed activities
4. **Preference Alignment**: Respect max activities per day preference
5. **Opening Hours**: Consider typical attraction schedules
6. **Logical Flow**: Morning activities first, evening ones later

## Output Format
Return a valid JSON object:
```json
{
    "optimized_schedule": [
        {
            "day": 1,
            "activities": [
                {"name": "Activity 1", "location": "Location", "suggested_time": "09:00-11:00"},
                {"name": "Activity 2", "location": "Location", "suggested_time": "14:00-16:00"}
            ],
            "notes": "Focus on central area attractions"
        }
    ],
    "changes_made": [
        "Grouped activities by neighborhood to reduce transit time",
        "Moved outdoor activities to morning for better weather"
    ],
    "time_saved": "Approximately 2 hours per day from optimized routing",
    "efficiency_score": 0.88
}
```

## Guidelines:
- Respect the maximum activities per day from preferences
- Group activities by geographic proximity
- Consider typical opening hours (museums often closed Mondays, etc.)
- Leave buffer time between activities for meals and rest
- efficiency_score is 0.0-1.0 based on how well optimized the schedule is

IMPORTANT: Return ONLY the JSON object, no markdown formatting or explanation."""


class AnalysisAgent:
    """
    Analysis agent for evaluating travel plans using LLM
    """

    def __init__(self, config=None):
        self.config = config or get_config()

    def analyze_itinerary_feasibility(
        self,
        itinerary: Dict[str, Any],
        constraints: Dict[str, Any]
    ) -> FeasibilityResult:
        """
        Analyze if the proposed itinerary is feasible using LLM

        Args:
            itinerary: Proposed itinerary with flights, hotels, activities
            constraints: User constraints (budget, time, preferences)

        Returns:
            FeasibilityResult with analysis
        """
        print("Analyzing itinerary feasibility with LLM...")
        print(f"  Using base_url: {self.config.llm.base_url}")
        print(f"  Using model: {self.config.llm.model}")

        # Build structured user content for better LLM understanding
        user_content = self._build_feasibility_content(itinerary, constraints)

        # Get LLM client
        client = self.config.get_llm_client(label="analyze_itinerary")

        try:
            messages = [
                {
                    "role": "system",
                    "content": FEASIBILITY_SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": user_content  # Array of {"type": "text", "text": ...}
                }
            ]

            try:
                response = client.chat.completions.create(
                    model=self.config.llm.model,
                    messages=messages,
                    response_format=get_response_format("feasibility_analysis", FEASIBILITY_ANALYSIS_SCHEMA),
                    temperature=0.3,
                    max_tokens=2000
                )
            except Exception as e:
                if "response_format" in str(e).lower():
                    # Fallback for models that don't support response_format
                    response = client.chat.completions.create(
                        model=self.config.llm.model,
                        messages=messages,
                        temperature=0.3,
                        max_tokens=2000
                    )
                else:
                    raise

            content = response.choices[0].message.content
            data = self._parse_llm_response(content)

            print("Feasibility analysis completed successfully")

            return FeasibilityResult(
                is_feasible=data.get("is_feasible", True),
                confidence=data.get("confidence", 0.7),
                issues=data.get("issues", []),
                warnings=data.get("warnings", []),
                suggestions=data.get("suggestions", []),
                schedule_analysis=data.get("schedule_analysis", {})
            )

        except Exception as e:
            print(f"LLM feasibility analysis failed: {str(e)}")
            return self._fallback_feasibility(itinerary, constraints)

    def analyze_cost_breakdown(
        self,
        flights: Dict[str, Any],
        hotels: Dict[str, Any],
        activities: List[Dict[str, Any]],
        budget: float,
        num_days: int = 5,
        currency: str = "USD"
    ) -> CostBreakdownResult:
        """
        Analyze cost breakdown of the trip using LLM

        Args:
            flights: Flight information with prices
            hotels: Hotel information with prices
            activities: List of planned activities
            budget: Total budget
            num_days: Number of days
            currency: Currency code

        Returns:
            CostBreakdownResult with detailed breakdown
        """
        print("Analyzing cost breakdown with LLM...")

        # Build structured user content for better LLM understanding
        user_content = self._build_cost_content(flights, hotels, activities, budget, num_days, currency)

        # Get LLM client
        client = self.config.get_llm_client(label="analyze_cost")

        try:
            messages = [
                {
                    "role": "system",
                    "content": COST_ANALYSIS_SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": user_content  # Array of {"type": "text", "text": ...}
                }
            ]

            try:
                response = client.chat.completions.create(
                    model=self.config.llm.model,
                    messages=messages,
                    response_format=get_response_format("cost_breakdown", COST_BREAKDOWN_SCHEMA),
                    temperature=0.3,
                    max_tokens=2000
                )
            except Exception as e:
                if "response_format" in str(e).lower():
                    # Fallback for models that don't support response_format
                    response = client.chat.completions.create(
                        model=self.config.llm.model,
                        messages=messages,
                        temperature=0.3,
                        max_tokens=2000
                    )
                else:
                    raise

            content = response.choices[0].message.content
            data = self._parse_llm_response(content)

            print("Cost analysis completed successfully")

            return CostBreakdownResult(
                total_estimated_cost=data.get("total_estimated_cost", 0),
                currency=data.get("currency", currency),
                breakdown=data.get("breakdown", {}),
                within_budget=data.get("within_budget", True),
                budget_remaining=data.get("budget_remaining", 0),
                cost_saving_tips=data.get("cost_saving_tips", [])
            )

        except Exception as e:
            print(f"LLM cost analysis failed: {str(e)}")
            return self._fallback_cost_breakdown(flights, hotels, activities, budget, num_days, currency)

    def analyze_schedule_optimization(
        self,
        activities: List[Dict[str, Any]],
        preferences: List[str],
        num_days: int = 5,
        research_context: Optional[Dict[str, Any]] = None
    ) -> ScheduleOptimizationResult:
        """
        Optimize the activity schedule using LLM

        Args:
            activities: List of planned activities
            preferences: User preferences
            num_days: Number of days
            research_context: Optional context with destination, hotels, flights, restaurants

        Returns:
            ScheduleOptimizationResult with optimized schedule
        """
        print("Optimizing schedule with LLM...")

        # Build structured user content for better LLM understanding
        user_content = self._build_schedule_content(activities, preferences, num_days, research_context)

        # Get LLM client
        client = self.config.get_llm_client(label="analysis_schedule")

        try:
            messages = [
                {
                    "role": "system",
                    "content": SCHEDULE_OPTIMIZATION_SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": user_content  # Array of {"type": "text", "text": ...}
                }
            ]

            try:
                response = client.chat.completions.create(
                    model=self.config.llm.model,
                    messages=messages,
                    response_format=get_response_format("schedule_optimization", SCHEDULE_OPTIMIZATION_SCHEMA),
                    temperature=0.3,
                    max_tokens=2000
                )
            except Exception as e:
                if "response_format" in str(e).lower():
                    # Fallback for models that don't support response_format
                    response = client.chat.completions.create(
                        model=self.config.llm.model,
                        messages=messages,
                        temperature=0.3,
                        max_tokens=2000
                    )
                else:
                    raise

            content = response.choices[0].message.content
            data = self._parse_llm_response(content)

            print("Schedule optimization completed successfully")

            return ScheduleOptimizationResult(
                optimized_schedule=data.get("optimized_schedule", []),
                changes_made=data.get("changes_made", []),
                time_saved=data.get("time_saved", ""),
                efficiency_score=data.get("efficiency_score", 0.8)
            )

        except Exception as e:
            print(f"LLM schedule optimization failed: {str(e)}")
            return self._fallback_schedule_optimization(activities, preferences, num_days)

    def _build_feasibility_content(
        self,
        itinerary: Dict,
        constraints: Dict
    ) -> List[Dict[str, Any]]:
        """
        Build structured content array for feasibility analysis.

        Returns an array of content parts for better LLM understanding:
        - Separates itinerary from constraints
        - Uses JSON for structured data
        """
        content_parts = []

        # Part 1: Itinerary as JSON
        sanitized_itinerary = self._strip_base64_from_data(itinerary)
        content_parts.append({
            "type": "text",
            "text": f"## Itinerary\n\n```json\n{json.dumps(sanitized_itinerary, indent=2, default=str)}\n```"
        })

        # Part 2: Constraints as JSON
        constraint_data = {
            "budget": constraints.get("budget", "Not specified"),
            "preferences": constraints.get("preferences", []),
            "hard_constraints": constraints.get("hard_constraints", [])
        }
        content_parts.append({
            "type": "text",
            "text": f"## Constraints\n\n```json\n{json.dumps(constraint_data, indent=2)}\n```"
        })

        # Part 3: Task instruction
        content_parts.append({
            "type": "text",
            "text": "## Task\n\nAnalyze the feasibility of this travel itinerary against the constraints."
        })

        return content_parts

    def _build_cost_content(
        self,
        flights: Dict,
        hotels: Dict,
        activities: List[Dict],
        budget: float,
        num_days: int,
        currency: str
    ) -> List[Dict[str, Any]]:
        """
        Build structured content array for cost analysis.

        Returns an array of content parts for better LLM understanding:
        - Separates trip info, flights, hotels, and activities
        - Uses JSON for structured data
        """
        content_parts = []

        # Part 1: Trip info as JSON
        trip_info = {
            "budget": budget,
            "currency": currency,
            "num_days": num_days,
            "num_nights": num_days - 1
        }
        content_parts.append({
            "type": "text",
            "text": f"## Trip Info\n\n```json\n{json.dumps(trip_info, indent=2)}\n```"
        })

        # Part 2: Flight data as JSON
        sanitized_flights = self._strip_base64_from_data(flights)
        content_parts.append({
            "type": "text",
            "text": f"## Flight Data\n\n```json\n{json.dumps(sanitized_flights, indent=2, default=str)}\n```"
        })

        # Part 3: Hotel data as JSON
        sanitized_hotels = self._strip_base64_from_data(hotels)
        content_parts.append({
            "type": "text",
            "text": f"## Hotel Data\n\n```json\n{json.dumps(sanitized_hotels, indent=2, default=str)}\n```"
        })

        # Part 4: Activities as JSON
        sanitized_activities = self._strip_base64_from_data(activities)
        content_parts.append({
            "type": "text",
            "text": f"## Activities\n\n```json\n{json.dumps(sanitized_activities, indent=2, default=str)}\n```"
        })

        # Part 5: Task instruction
        content_parts.append({
            "type": "text",
            "text": "## Task\n\nAnalyze the cost breakdown for this trip and provide budget recommendations."
        })

        return content_parts

    def _build_schedule_content(
        self,
        activities: List[Dict],
        preferences: List[str],
        num_days: int,
        research_context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Build structured content array for schedule optimization.

        Returns an array of content parts for better LLM understanding:
        - Includes destination info, hotels, flights from research context
        - Separates trip duration, preferences, and activities
        - Uses JSON for structured data
        """
        content_parts = []

        # Part 1: Trip context from research (destination, dates, flights, hotels)
        if research_context:
            trip_context = {
                "destination": research_context.get("destination", "Unknown"),
                "dates": {
                    "start": research_context.get("start_date"),
                    "end": research_context.get("end_date")
                }
            }

            # Add flight info if available
            if research_context.get("flights"):
                flights = research_context["flights"]
                trip_context["flights"] = {
                    "outbound": self._extract_flight_summary(flights.get("best_outbound")),
                    "return": self._extract_flight_summary(flights.get("best_return"))
                }

            # Add hotel info if available
            if research_context.get("hotels"):
                hotels = research_context["hotels"]
                best_hotel = hotels.get("best_value") or (hotels.get("hotels", [{}])[0] if hotels.get("hotels") else {})
                trip_context["accommodation"] = {
                    "name": best_hotel.get("name"),
                    "location": best_hotel.get("location"),
                    "check_in_time": "15:00",  # Standard check-in
                    "check_out_time": "11:00"  # Standard check-out
                }

            # Add restaurant info if available
            if research_context.get("restaurants"):
                restaurants = research_context["restaurants"]
                restaurant_list = restaurants.get("restaurants", [])[:5]
                trip_context["dining_options"] = [
                    {"name": r.get("name"), "cuisine": r.get("cuisine"), "location": r.get("location")}
                    for r in restaurant_list
                ]

            content_parts.append({
                "type": "text",
                "text": f"## Trip Context\n\n```json\n{json.dumps(trip_context, indent=2, default=str)}\n```"
            })

        # Part 2: Trip duration and preferences as JSON
        schedule_params = {
            "num_days": num_days,
            "preferences": preferences
        }
        content_parts.append({
            "type": "text",
            "text": f"## Schedule Parameters\n\n```json\n{json.dumps(schedule_params, indent=2)}\n```"
        })

        # Part 3: Activities as JSON
        sanitized_activities = self._strip_base64_from_data(activities)
        content_parts.append({
            "type": "text",
            "text": f"## Activities to Schedule\n\n```json\n{json.dumps(sanitized_activities, indent=2, default=str)}\n```"
        })

        # Part 3: Task instruction
        content_parts.append({
            "type": "text",
            "text": "## Task\n\nOptimize this activity schedule for maximum efficiency and enjoyment."
        })

        return content_parts

    def _extract_flight_summary(self, flight: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Extract a summary of flight info for context."""
        if not flight:
            return None
        return {
            "airline": flight.get("airline"),
            "departure_time": flight.get("departure_time"),
            "arrival_time": flight.get("arrival_time"),
            "duration": flight.get("duration")
        }

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

    def _fallback_feasibility(
        self,
        itinerary: Dict[str, Any],
        constraints: Dict[str, Any]
    ) -> FeasibilityResult:
        """Fallback feasibility analysis if LLM fails"""
        return FeasibilityResult(
            is_feasible=True,
            confidence=0.6,
            issues=[],
            warnings=["Unable to perform detailed analysis - review manually"],
            suggestions=["Verify all constraints are met"],
            schedule_analysis={
                "total_days": itinerary.get("total_days", 5),
                "activities_per_day": itinerary.get("activities_per_day", 2),
                "note": "Fallback analysis - LLM unavailable"
            }
        )

    def _fallback_cost_breakdown(
        self,
        flights: Dict[str, Any],
        hotels: Dict[str, Any],
        activities: List[Dict[str, Any]],
        budget: float,
        num_days: int,
        currency: str
    ) -> CostBreakdownResult:
        """Fallback cost analysis if LLM fails"""
        # Calculate basic costs from data
        flight_cost = 0
        if flights:
            outbound = flights.get("best_outbound", {})
            return_flight = flights.get("best_return", {})
            flight_cost = outbound.get("price", 0) + return_flight.get("price", 0)

        hotel_cost = 0
        if hotels:
            best_hotel = hotels.get("best_value", {})
            per_night = best_hotel.get("price_per_night", 0)
            hotel_cost = per_night * (num_days - 1)

        activity_cost = sum(act.get("price", 0) for act in activities)

        breakdown = {
            "flights": flight_cost,
            "accommodation": hotel_cost,
            "activities": activity_cost,
            "food_and_transport": 0,
            "miscellaneous": 0
        }

        total = sum(breakdown.values())

        return CostBreakdownResult(
            total_estimated_cost=round(total, 2),
            currency=currency,
            breakdown={k: round(v, 2) for k, v in breakdown.items()},
            within_budget=total <= budget,
            budget_remaining=round(budget - total, 2),
            cost_saving_tips=["Fallback analysis - review costs manually"]
        )

    def _fallback_schedule_optimization(
        self,
        activities: List[Dict[str, Any]],
        preferences: List[str],
        num_days: int
    ) -> ScheduleOptimizationResult:
        """Fallback schedule optimization if LLM fails"""
        max_per_day = 2

        # Extract max from preferences
        for pref in preferences:
            if "no more than" in pref.lower() and "activities" in pref.lower():
                import re
                match = re.search(r'(\d+)', pref)
                if match:
                    max_per_day = int(match.group(1))

        # Simple distribution
        optimized = []
        remaining = activities.copy()

        for day in range(1, num_days + 1):
            day_acts = remaining[:max_per_day]
            remaining = remaining[max_per_day:]
            optimized.append({
                "day": day,
                "activities": day_acts,
                "notes": f"Day {day}"
            })

        return ScheduleOptimizationResult(
            optimized_schedule=optimized,
            changes_made=["Fallback analysis - basic distribution only"],
            time_saved="Unknown",
            efficiency_score=0.6
        )
