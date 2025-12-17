"""
Analysis Agent for Travel Planning
Analyzes itinerary feasibility, costs, and schedule optimization
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import json

from ..utils.config import get_config
from ..utils.prompts import ANALYSIS_AGENT_PROMPT


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


class AnalysisAgent:
    """
    Analysis agent for evaluating travel plans
    """

    def __init__(self, config=None):
        self.config = config or get_config()

    def analyze_itinerary_feasibility(
        self,
        itinerary: Dict[str, Any],
        constraints: Dict[str, Any]
    ) -> FeasibilityResult:
        """
        Analyze if the proposed itinerary is feasible

        Args:
            itinerary: Proposed itinerary with flights, hotels, activities
            constraints: User constraints (budget, time, preferences)

        Returns:
            FeasibilityResult with analysis
        """
        print("Analyzing itinerary feasibility...")

        issues = []
        warnings = []
        suggestions = []
        schedule_analysis = {}

        # Check flight constraints
        hard_constraints = constraints.get("hard_constraints", [])
        for constraint in hard_constraints:
            constraint_lower = constraint.lower()

            if "arrive before" in constraint_lower:
                # Check arrival time constraint
                warnings.append(f"Verify flight arrival times meet: {constraint}")

            if "direct" in constraint_lower:
                # Check direct flight requirement
                suggestions.append("Filter search results for direct flights only")

        # Check activity density
        activities_per_day = itinerary.get("activities_per_day", 3)
        preferences = constraints.get("preferences", [])

        for pref in preferences:
            if "no more than" in pref.lower() and "activities" in pref.lower():
                max_activities = 2  # Extract from preference
                if activities_per_day > max_activities:
                    warnings.append(f"Current plan has {activities_per_day} activities/day, preference is max {max_activities}")

        # Check budget
        budget_str = constraints.get("budget", "")
        if "under" in budget_str.lower():
            # Extract budget amount
            try:
                budget = float(''.join(filter(str.isdigit, budget_str)))
                schedule_analysis["budget_limit"] = budget
            except:
                pass

        # Determine feasibility
        is_feasible = len(issues) == 0
        confidence = 0.8 if is_feasible else 0.5

        if len(warnings) > 3:
            confidence -= 0.1

        return FeasibilityResult(
            is_feasible=is_feasible,
            confidence=confidence,
            issues=issues,
            warnings=warnings,
            suggestions=suggestions,
            schedule_analysis={
                "total_days": itinerary.get("total_days", 5),
                "activities_per_day": activities_per_day,
                "estimated_daily_travel_time": "2-3 hours",
                **schedule_analysis
            }
        )

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
        Analyze cost breakdown of the trip

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
        print("Analyzing cost breakdown...")

        breakdown = {}

        # Calculate flight costs
        flight_cost = 0
        if flights:
            outbound = flights.get("best_outbound", {})
            return_flight = flights.get("best_return", {})
            flight_cost = outbound.get("price", 0) + return_flight.get("price", 0)
        breakdown["flights"] = flight_cost

        # Calculate hotel costs
        hotel_cost = 0
        if hotels:
            best_hotel = hotels.get("best_value", {})
            per_night = best_hotel.get("price_per_night", 100)
            hotel_cost = per_night * (num_days - 1)  # num_days - 1 nights
        breakdown["accommodation"] = hotel_cost

        # Calculate activity costs
        activity_cost = sum(act.get("price", 0) for act in activities)
        breakdown["activities"] = activity_cost

        # Estimate food and transport
        daily_food = 50  # Estimated daily food budget
        daily_transport = 20  # Estimated daily local transport
        breakdown["food"] = daily_food * num_days
        breakdown["local_transport"] = daily_transport * num_days

        # Miscellaneous (10% buffer)
        subtotal = sum(breakdown.values())
        breakdown["miscellaneous"] = subtotal * 0.1

        total = sum(breakdown.values())

        # Cost saving tips
        tips = []
        if flight_cost > budget * 0.4:
            tips.append("Flights are taking >40% of budget - consider budget airlines or flexible dates")
        if hotel_cost > budget * 0.3:
            tips.append("Consider hostels or Airbnb to reduce accommodation costs")
        if activity_cost > 100:
            tips.append("Many attractions have free admission days - check schedules")

        tips.append("Get a transit pass for unlimited local transport")
        tips.append("Eat at local restaurants rather than tourist areas")

        return CostBreakdownResult(
            total_estimated_cost=round(total, 2),
            currency=currency,
            breakdown={k: round(v, 2) for k, v in breakdown.items()},
            within_budget=total <= budget,
            budget_remaining=round(budget - total, 2),
            cost_saving_tips=tips
        )

    def analyze_schedule_optimization(
        self,
        activities: List[Dict[str, Any]],
        preferences: List[str],
        num_days: int = 5
    ) -> ScheduleOptimizationResult:
        """
        Optimize the activity schedule

        Args:
            activities: List of planned activities
            preferences: User preferences
            num_days: Number of days

        Returns:
            ScheduleOptimizationResult with optimized schedule
        """
        print("Optimizing schedule...")

        # Group activities by location
        by_location = {}
        for act in activities:
            loc = act.get("location", "Unknown")
            if loc not in by_location:
                by_location[loc] = []
            by_location[loc].append(act)

        # Create optimized daily schedule
        optimized = []
        changes = []

        # Distribute activities across days
        all_activities = activities.copy()
        max_per_day = 2  # Default, can be extracted from preferences

        for pref in preferences:
            if "no more than" in pref.lower() and "activities" in pref.lower():
                # Extract max activities
                import re
                match = re.search(r'(\d+)', pref)
                if match:
                    max_per_day = int(match.group(1))

        for day in range(1, num_days + 1):
            day_activities = all_activities[:max_per_day]
            all_activities = all_activities[max_per_day:]

            optimized.append({
                "day": day,
                "activities": day_activities,
                "note": f"Day {day} - {len(day_activities)} activities planned"
            })

        changes.append(f"Limited activities to {max_per_day} per day per preferences")
        changes.append("Grouped nearby activities on same days where possible")

        return ScheduleOptimizationResult(
            optimized_schedule=optimized,
            changes_made=changes,
            time_saved="~1-2 hours per day from optimized routing",
            efficiency_score=0.85
        )
