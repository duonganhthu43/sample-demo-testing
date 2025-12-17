"""
Itinerary Agent for Travel Planning
Generates comprehensive day-by-day travel itineraries
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
import json

from ..utils.config import get_config
from ..utils.prompts import ITINERARY_AGENT_PROMPT


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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "destination": self.destination,
            "travel_dates": self.travel_dates,
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


class ItineraryAgent:
    """
    Agent for generating travel itineraries
    """

    def __init__(self, config=None):
        self.config = config or get_config()

    def generate_itinerary(
        self,
        context: Dict[str, Any]
    ) -> ItineraryResult:
        """
        Generate a comprehensive itinerary from gathered context

        Args:
            context: All gathered research and analysis results

        Returns:
            ItineraryResult with day-by-day plan
        """
        print("Generating comprehensive itinerary...")

        # Extract information from context
        destination = context.get("destination", "Unknown")
        travel_dates = context.get("travel_dates", "")
        num_days = context.get("num_days", 5)
        constraints = context.get("constraints", {})

        # Get research results
        research = context.get("research", [])
        all_activities = []
        food_activities = []
        flights = {}
        hotels = {}
        destination_info = {}

        for item in research:
            if item.get("type") == "activities":
                all_activities = item.get("activities", [])
                # Separate food activities
                for act in all_activities:
                    if act.get("category", "").lower() == "food":
                        food_activities.append(act)
            if item.get("type") == "flights":
                flights = item
            if item.get("type") == "accommodations":
                hotels = item
            if item.get("type") == "destination":
                destination_info = item

        # Filter non-food activities for main schedule
        activities = [a for a in all_activities if a.get("category", "").lower() != "food"]

        # Get weather info
        weather = context.get("weather", {})
        packing = weather.get("packing_suggestions", [])

        # Get cost analysis if available
        cost_analysis = self._get_cost_analysis(context)

        # Generate day-by-day itinerary
        days = []
        activity_index = 0
        food_index = 0

        for day_num in range(1, num_days + 1):
            day_activities = []

            # Assign 2-3 activities per day based on preferences
            max_activities = self._get_max_activities_per_day(constraints)
            for _ in range(max_activities):
                if activity_index < len(activities):
                    day_activities.append(activities[activity_index])
                    activity_index += 1

            day_plan = {
                "day": day_num,
                "date": f"Day {day_num}",
                "theme": self._get_day_theme(day_num, num_days, day_activities),
                "schedule": []
            }

            # Morning activity
            if day_activities:
                morning_act = day_activities[0]
                day_plan["schedule"].append({
                    "time": "09:00 - 12:00",
                    "activity": morning_act.get("name", "Morning exploration"),
                    "location": morning_act.get("location", destination),
                    "category": morning_act.get("category", "Sightseeing"),
                    "notes": self._get_activity_notes(morning_act),
                    "cost": morning_act.get("price", 0),
                    "source_url": morning_act.get("source_url")
                })

            # Lunch - use food activities or destination-specific recommendations
            lunch_info = self._get_meal_recommendation(
                food_activities, food_index, destination, "lunch", destination_info
            )
            day_plan["schedule"].append({
                "time": "12:00 - 13:30",
                "activity": lunch_info["name"],
                "location": lunch_info["location"],
                "category": "Food",
                "notes": lunch_info["notes"],
                "cost": lunch_info["cost"],
                "source_url": lunch_info.get("source_url")
            })
            if lunch_info.get("from_food_activities"):
                food_index += 1

            # Afternoon activity
            if len(day_activities) > 1:
                afternoon_act = day_activities[1]
                day_plan["schedule"].append({
                    "time": "14:00 - 17:00",
                    "activity": afternoon_act.get("name", "Afternoon exploration"),
                    "location": afternoon_act.get("location", destination),
                    "category": afternoon_act.get("category", "Sightseeing"),
                    "notes": self._get_activity_notes(afternoon_act),
                    "cost": afternoon_act.get("price", 0),
                    "source_url": afternoon_act.get("source_url")
                })

            # Optional late afternoon activity
            if len(day_activities) > 2:
                late_act = day_activities[2]
                day_plan["schedule"].append({
                    "time": "17:30 - 19:00",
                    "activity": late_act.get("name", "Evening activity"),
                    "location": late_act.get("location", destination),
                    "category": late_act.get("category", "Sightseeing"),
                    "notes": self._get_activity_notes(late_act),
                    "cost": late_act.get("price", 0),
                    "source_url": late_act.get("source_url")
                })

            # Dinner - use food activities or destination-specific recommendations
            dinner_info = self._get_meal_recommendation(
                food_activities, food_index, destination, "dinner", destination_info
            )
            day_plan["schedule"].append({
                "time": "19:00 - 21:00",
                "activity": dinner_info["name"],
                "location": dinner_info["location"],
                "category": "Food",
                "notes": dinner_info["notes"],
                "cost": dinner_info["cost"],
                "source_url": dinner_info.get("source_url")
            })
            if dinner_info.get("from_food_activities"):
                food_index += 1

            # Calculate day total
            day_plan["day_cost"] = sum(
                item.get("cost", 0) for item in day_plan["schedule"]
            )

            days.append(day_plan)

        # Calculate total cost using actual data
        total_cost = self._calculate_total_cost(
            flights, hotels, all_activities, num_days, cost_analysis
        )

        # Important notes - dynamic based on context
        notes = self._generate_important_notes(
            destination, destination_info, weather, constraints
        )

        # Packing list - from weather + destination
        final_packing = self._generate_packing_list(packing, weather, destination_info)

        return ItineraryResult(
            destination=destination,
            travel_dates=travel_dates,
            days=days,
            total_estimated_cost=total_cost,
            currency="USD",
            summary=self._generate_summary_text(destination, num_days, all_activities, total_cost),
            packing_list=final_packing,
            important_notes=notes
        )

    def _get_max_activities_per_day(self, constraints: Dict) -> int:
        """Get max activities per day from preferences"""
        preferences = constraints.get("preferences", [])
        for pref in preferences:
            if "no more than" in pref.lower() and "activities" in pref.lower():
                # Extract number
                import re
                match = re.search(r'(\d+)', pref)
                if match:
                    return int(match.group(1))
        return 2  # Default

    def _get_activity_notes(self, activity: Dict) -> str:
        """Get notes for an activity"""
        tips = activity.get("tips", [])
        if tips and isinstance(tips, list):
            return tips[0] if tips else "Enjoy!"
        return str(tips) if tips else "Enjoy!"

    def _get_meal_recommendation(
        self,
        food_activities: List[Dict],
        food_index: int,
        destination: str,
        meal_type: str,
        destination_info: Dict
    ) -> Dict[str, Any]:
        """Get meal recommendation from context or generate based on destination"""

        # Try to use a food activity
        if food_index < len(food_activities):
            food_act = food_activities[food_index]
            return {
                "name": food_act.get("name", f"Local {meal_type}"),
                "location": food_act.get("location", destination),
                "notes": self._get_activity_notes(food_act),
                "cost": food_act.get("price", 20 if meal_type == "lunch" else 30),
                "source_url": food_act.get("source_url"),
                "from_food_activities": True
            }

        # Generate destination-specific recommendation
        local_cuisine = destination_info.get("local_cuisine", [])
        cuisine_tip = local_cuisine[0] if local_cuisine else f"local {destination} cuisine"

        # Destination-specific meal costs (estimates based on region)
        meal_costs = self._estimate_meal_cost(destination, meal_type)

        if meal_type == "lunch":
            return {
                "name": f"Lunch - Try {cuisine_tip}",
                "location": f"Local restaurant in {destination}",
                "notes": f"Explore local lunch spots, try {cuisine_tip}",
                "cost": meal_costs,
                "from_food_activities": False
            }
        else:
            return {
                "name": f"Dinner - {destination} dining experience",
                "location": f"Restaurant district, {destination}",
                "notes": f"Experience local dinner culture, consider {cuisine_tip}",
                "cost": meal_costs,
                "from_food_activities": False
            }

    def _estimate_meal_cost(self, destination: str, meal_type: str) -> float:
        """Estimate meal cost based on destination"""
        dest_lower = destination.lower()

        # Regional cost estimates (USD)
        expensive_cities = ["tokyo", "singapore", "hong kong", "london", "paris", "new york", "zurich"]
        moderate_cities = ["bangkok", "seoul", "taipei", "osaka", "berlin", "barcelona"]
        budget_cities = ["hanoi", "bali", "kuala lumpur", "manila", "jakarta"]

        if any(city in dest_lower for city in expensive_cities):
            return 20 if meal_type == "lunch" else 40
        elif any(city in dest_lower for city in moderate_cities):
            return 12 if meal_type == "lunch" else 25
        elif any(city in dest_lower for city in budget_cities):
            return 8 if meal_type == "lunch" else 15
        else:
            return 15 if meal_type == "lunch" else 30  # Default

    def _get_day_theme(self, day_num: int, total_days: int, day_activities: List) -> str:
        """Get theme for the day based on activities"""
        if day_num == 1:
            return "Arrival & Orientation"
        elif day_num == total_days:
            return "Final Exploration & Departure"

        # Determine theme from activities
        if day_activities:
            categories = [a.get("category", "").lower() for a in day_activities]
            if "cultural" in categories or "museum" in categories:
                return "Cultural Immersion"
            elif "nature" in categories or "adventure" in categories:
                return "Nature & Adventure"
            elif "shopping" in categories:
                return "Shopping & Local Life"
            elif "food" in categories:
                return "Culinary Exploration"

        return f"Day {day_num} Exploration"

    def _get_cost_analysis(self, context: Dict) -> Dict:
        """Extract cost analysis from context"""
        for item in context.get("analysis", []):
            if item.get("type") == "cost":
                return item
        return {}

    def _calculate_total_cost(
        self,
        flights: Dict,
        hotels: Dict,
        activities: List,
        num_days: int,
        cost_analysis: Dict
    ) -> float:
        """Calculate total trip cost from actual data"""
        cost = 0

        # Use cost analysis if available
        if cost_analysis.get("total_estimated"):
            return cost_analysis.get("total_estimated", 0)

        # Flights - use actual prices
        if flights:
            best_out = flights.get("best_outbound", {})
            best_ret = flights.get("best_return", {})
            cost += best_out.get("price", 0)
            cost += best_ret.get("price", 0)

            # If no best flights, estimate from options
            if cost == 0:
                outbound = flights.get("outbound_flights", [])
                return_flights = flights.get("return_flights", [])
                if outbound:
                    cost += outbound[0].get("price", 0)
                if return_flights:
                    cost += return_flights[0].get("price", 0)

        # Hotels - use actual prices
        if hotels:
            best_hotel = hotels.get("best_value") or hotels.get("highest_rated", {})
            per_night = best_hotel.get("price_per_night", 0)
            if per_night > 0:
                cost += per_night * (num_days - 1)
            else:
                # Estimate from hotel list
                hotel_list = hotels.get("hotels", [])
                if hotel_list:
                    avg_price = sum(h.get("price_per_night", 0) for h in hotel_list) / len(hotel_list)
                    cost += avg_price * (num_days - 1)

        # Activities - sum actual prices
        activity_cost = sum(a.get("price", 0) for a in activities)
        cost += activity_cost

        # Food & local transport - estimate based on destination
        daily_misc = self._estimate_daily_misc_cost(activities)
        cost += daily_misc * num_days

        return round(cost, 2)

    def _estimate_daily_misc_cost(self, activities: List) -> float:
        """Estimate daily food and transport cost"""
        # Calculate average activity price to gauge destination cost level
        if activities:
            avg_activity = sum(a.get("price", 0) for a in activities) / len(activities)
            if avg_activity > 50:
                return 80  # Expensive destination
            elif avg_activity > 20:
                return 50  # Moderate destination
            else:
                return 35  # Budget destination
        return 50  # Default

    def _generate_important_notes(
        self,
        destination: str,
        destination_info: Dict,
        weather: Dict,
        constraints: Dict
    ) -> List[str]:
        """Generate important notes based on context"""
        notes = []

        # Visa/entry requirements
        visa_info = destination_info.get("visa_requirements", "")
        if visa_info:
            notes.append(f"Visa: {visa_info}")

        # Weather-specific
        if weather:
            rain_chance = weather.get("summary", {}).get("average_rain_chance", 0)
            if rain_chance > 40:
                notes.append("Rain likely - pack umbrella and waterproof jacket")

            avg_temp = weather.get("summary", {}).get("average_temp")
            if avg_temp:
                if avg_temp > 30:
                    notes.append("Hot weather expected - stay hydrated, avoid midday sun")
                elif avg_temp < 10:
                    notes.append("Cold weather - pack warm layers")

        # Constraint-specific
        hard_constraints = constraints.get("hard_constraints", [])
        for constraint in hard_constraints:
            notes.append(f"Important: {constraint}")

        # General travel tips
        notes.extend([
            "Download offline maps before departure",
            "Keep digital copies of important documents",
            "Notify bank of travel dates"
        ])

        return notes[:8]  # Limit to 8 notes

    def _generate_packing_list(
        self,
        weather_packing: List[str],
        weather: Dict,
        destination_info: Dict
    ) -> List[str]:
        """Generate comprehensive packing list"""
        packing = set(weather_packing) if weather_packing else set()

        # Essentials
        packing.update([
            "Passport and copies",
            "Comfortable walking shoes",
            "Phone charger and adapter"
        ])

        # Weather-based
        if weather:
            avg_temp = weather.get("summary", {}).get("average_temp", 20)
            if avg_temp > 25:
                packing.update(["Sunscreen", "Sunglasses", "Light breathable clothing"])
            elif avg_temp < 15:
                packing.update(["Warm jacket", "Layers", "Scarf"])

            if weather.get("summary", {}).get("average_rain_chance", 0) > 30:
                packing.add("Umbrella or rain jacket")

        # Destination-specific
        culture_tips = destination_info.get("culture_tips", [])
        if any("temple" in tip.lower() or "modest" in tip.lower() for tip in culture_tips):
            packing.add("Modest clothing for temples/religious sites")

        return list(packing)[:15]  # Limit to 15 items

    def _generate_summary_text(
        self,
        destination: str,
        num_days: int,
        activities: List,
        total_cost: float
    ) -> str:
        """Generate summary text"""
        activity_count = len(activities)
        categories = list(set(a.get("category", "Various") for a in activities))[:3]
        cat_text = ", ".join(categories) if categories else "various"

        return (
            f"{num_days}-day trip to {destination} featuring {activity_count} planned activities "
            f"including {cat_text}. Estimated total cost: ${total_cost:.0f} USD."
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

        # Extract highlights from actual activities
        highlights = []
        for day in days:
            for item in day.get("schedule", []):
                if item.get("category") not in ["Food"]:
                    highlights.append(f"Day {day['day']}: {item['activity']}")

        # Get cost breakdown from analysis
        cost_breakdown = self._get_cost_breakdown(context, total_cost)

        # Budget summary with actual breakdown
        budget_summary = {
            "total_estimated": total_cost,
            "currency": "USD",
            "breakdown": cost_breakdown
        }

        # Key bookings from actual research
        bookings = self._get_key_bookings(context)

        # Destination-specific checklist
        checklist = self._get_preparation_checklist(context, destination)

        return SummaryResult(
            trip_overview=f"A {len(days)}-day adventure to {destination} featuring cultural experiences, local cuisine, and memorable sightseeing.",
            highlights=highlights[:5],
            budget_summary=budget_summary,
            key_bookings=bookings,
            preparation_checklist=checklist
        )

    def _get_cost_breakdown(self, context: Dict, total: float) -> Dict:
        """Get cost breakdown from context or estimate"""
        for item in context.get("analysis", []):
            if item.get("type") == "cost" and item.get("breakdown"):
                return item.get("breakdown")

        # Estimate breakdown
        return {
            "flights": f"~${total * 0.30:.0f}",
            "accommodation": f"~${total * 0.25:.0f}",
            "activities": f"~${total * 0.15:.0f}",
            "food": f"~${total * 0.20:.0f}",
            "transport_misc": f"~${total * 0.10:.0f}"
        }

    def _get_key_bookings(self, context: Dict) -> List[Dict]:
        """Get key bookings needed"""
        bookings = []

        # Check for flight info
        for item in context.get("research", []):
            if item.get("type") == "flights":
                best = item.get("best_outbound", {})
                bookings.append({
                    "type": "Flight",
                    "details": f"{best.get('airline', 'TBD')} - ${best.get('price', 'TBD')}",
                    "status": "Book in advance",
                    "priority": "High"
                })
            if item.get("type") == "accommodations":
                best = item.get("best_value") or item.get("highest_rated", {})
                bookings.append({
                    "type": "Hotel",
                    "details": f"{best.get('name', 'TBD')} - ${best.get('price_per_night', 'TBD')}/night",
                    "status": "Book in advance",
                    "priority": "High"
                })

        # Add activity bookings
        bookings.append({
            "type": "Popular attractions",
            "details": "Check ticket availability",
            "status": "Book 1-2 weeks ahead",
            "priority": "Medium"
        })

        return bookings

    def _get_preparation_checklist(self, context: Dict, destination: str) -> List[str]:
        """Generate preparation checklist based on destination"""
        checklist = [
            "Check passport validity (6+ months required)",
        ]

        # Add visa check from destination info
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
            "Notify bank of travel dates",
            "Download offline maps and translation app",
            "Research local customs and etiquette",
            "Check weather forecast closer to date",
            "Pack according to packing list",
            "Print/save important confirmations",
            "Arrange airport transportation"
        ])

        return checklist
