"""
JSON Schema definitions for Structured Outputs - Travel Planning Agent

These schemas are used with OpenAI's structured outputs feature to ensure
the LLM always returns valid, schema-compliant JSON responses.

Reference: https://platform.openai.com/docs/guides/structured-outputs
"""

from typing import Dict, Any


def get_response_format(schema_name: str, schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a response_format dict for structured outputs.

    Args:
        schema_name: Name identifier for the schema
        schema: JSON schema definition

    Returns:
        response_format dict for OpenAI API
    """
    return {
        "type": "json_schema",
        "json_schema": {
            "name": schema_name,
            "schema": schema,
            "strict": True
        }
    }


# ============================================================================
# Itinerary Schema
# ============================================================================

ITINERARY_SCHEMA = {
    "type": "object",
    "properties": {
        "days": {
            "type": "array",
            "description": "Array of day-by-day itinerary plans",
            "items": {
                "type": "object",
                "properties": {
                    "day": {
                        "type": "integer",
                        "description": "Day number (1, 2, 3, etc.)"
                    },
                    "date": {
                        "type": "string",
                        "description": "Display date like 'Day 1' or actual date if known"
                    },
                    "theme": {
                        "type": "string",
                        "description": "Theme for the day (e.g., 'Arrival & First Impressions', 'Cultural Immersion', 'Food Exploration')"
                    },
                    "schedule": {
                        "type": "array",
                        "description": "List of activities/events for this day in chronological order",
                        "items": {
                            "type": "object",
                            "properties": {
                                "time": {
                                    "type": "string",
                                    "description": "Time range in 24h format (e.g., '09:00 - 11:00', '12:30 - 14:00')"
                                },
                                "activity": {
                                    "type": "string",
                                    "description": "Activity name (e.g., 'Visit Sensoji Temple', 'Lunch at Tsukiji Market', 'Flight to Tokyo')"
                                },
                                "description": {
                                    "type": "string",
                                    "description": "Detailed 2-3 sentence description. For FLIGHTS: include airport arrival time (3hrs before international), passport reminder, flight duration, arrival time, transport from airport with costs. For ATTRACTIONS: what you'll experience, opening hours, how to get there with transport cost. For MEALS: restaurant name near current area, cuisine type, 2-3 recommended dishes, price per person, reservation requirements, wait time."
                                },
                                "location": {
                                    "type": "string",
                                    "description": "Specific location. For MEALS: include full address if available (e.g., '1-22-7 Jinnan, Shibuya, Tokyo'). For ATTRACTIONS: area and district (e.g., 'Asakusa, Tokyo'). For TRANSPORT: station/airport name."
                                },
                                "category": {
                                    "type": "string",
                                    "description": "One of: Flight, Sightseeing, Cultural, Food, Shopping, Entertainment, Transport, Hotel"
                                },
                                "notes": {
                                    "type": "string",
                                    "description": "Practical tips (e.g., 'Arrive early to avoid crowds', 'Cash only', 'Reservation recommended')"
                                },
                                "cost": {
                                    "type": "number",
                                    "description": "Estimated cost in USD. For meals, use per-person cost. Use 0 for free activities."
                                },
                                "source_url": {
                                    "type": "string",
                                    "description": "URL source if available from research data, otherwise empty string"
                                },
                                "image_suggestion": {
                                    "type": "string",
                                    "description": "Image placeholder key in lowercase_snake_case for landmarks, attractions, AND restaurants (e.g., 'sensoji_temple', 'ichiran_shibuya', 'tsuta_ramen'). Use empty string only for transport/flights."
                                }
                            },
                            "required": ["time", "activity", "description", "location", "category", "notes", "cost", "source_url", "image_suggestion"],
                            "additionalProperties": False
                        }
                    },
                    "day_cost": {
                        "type": "number",
                        "description": "Total estimated cost for this day in USD (sum of all activity costs)"
                    }
                },
                "required": ["day", "date", "theme", "schedule", "day_cost"],
                "additionalProperties": False
            }
        },
        "total_estimated_cost": {
            "type": "number",
            "description": "Total trip cost in USD including flights, hotels, activities, food, and transport"
        },
        "summary": {
            "type": "string",
            "description": "Brief 1-2 sentence trip summary highlighting the destination and key experiences"
        },
        "packing_list": {
            "type": "array",
            "description": "List of items to pack based on weather and destination (clothing, essentials, destination-specific items)",
            "items": {"type": "string"}
        },
        "important_notes": {
            "type": "array",
            "description": "Critical information: visa requirements, weather warnings, cultural tips, safety info, hard constraints",
            "items": {"type": "string"}
        }
    },
    "required": ["days", "total_estimated_cost", "summary", "packing_list", "important_notes"],
    "additionalProperties": False
}


# ============================================================================
# Destination Extraction Schema
# ============================================================================

DESTINATION_EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "overview": {
            "type": "string",
            "description": "2-3 sentence overview of the destination highlighting its main attractions and character"
        },
        "visa_requirements": {
            "type": "string",
            "description": "Visa requirements for tourists including duration and any special requirements"
        },
        "best_time_to_visit": {
            "type": "string",
            "description": "Best months/seasons to visit with reasoning"
        },
        "language": {
            "type": "string",
            "description": "Official language(s) and English proficiency level"
        },
        "currency": {
            "type": "string",
            "description": "Local currency name and code (e.g., 'Japanese Yen (JPY)')"
        },
        "time_zone": {
            "type": "string",
            "description": "Timezone abbreviation and UTC offset (e.g., 'JST (UTC+9)')"
        },
        "cultural_tips": {
            "type": "array",
            "description": "4-5 practical cultural tips for tourists",
            "items": {"type": "string"}
        },
        "safety_rating": {
            "type": "string",
            "description": "Safety rating: Very Safe, Safe, Moderate, or Exercise Caution"
        },
        "local_cuisine": {
            "type": "array",
            "description": "3-5 must-try local dishes",
            "items": {"type": "string"}
        }
    },
    "required": [
        "overview", "visa_requirements", "best_time_to_visit",
        "language", "currency", "time_zone", "cultural_tips",
        "safety_rating", "local_cuisine"
    ],
    "additionalProperties": False
}


# ============================================================================
# Weather Forecast Schema
# ============================================================================

WEATHER_FORECAST_SCHEMA = {
    "type": "object",
    "properties": {
        "daily_forecast": {
            "type": "array",
            "description": "Daily weather forecasts for the trip duration",
            "items": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format or 'Day N'"
                    },
                    "condition": {
                        "type": "string",
                        "description": "Weather condition (Sunny, Cloudy, Rainy, etc.)"
                    },
                    "high_temp_celsius": {
                        "type": "integer",
                        "description": "High temperature in Celsius"
                    },
                    "low_temp_celsius": {
                        "type": "integer",
                        "description": "Low temperature in Celsius"
                    },
                    "precipitation_chance": {
                        "type": "integer",
                        "description": "Chance of rain/precipitation as percentage (0-100)"
                    },
                    "humidity": {
                        "type": "integer",
                        "description": "Humidity percentage (0-100)"
                    },
                    "recommendation": {
                        "type": "string",
                        "description": "Activity recommendation based on weather (e.g., 'Good for outdoor activities')"
                    }
                },
                "required": [
                    "date", "condition", "high_temp_celsius", "low_temp_celsius",
                    "precipitation_chance", "humidity", "recommendation"
                ],
                "additionalProperties": False
            }
        },
        "summary": {
            "type": "object",
            "description": "Overall weather summary for the trip",
            "properties": {
                "average_high": {
                    "type": "number",
                    "description": "Average high temperature in Celsius"
                },
                "average_low": {
                    "type": "number",
                    "description": "Average low temperature in Celsius"
                },
                "average_rain_chance": {
                    "type": "number",
                    "description": "Average precipitation chance as percentage"
                },
                "overall_recommendation": {
                    "type": "string",
                    "description": "Overall weather assessment and recommendation"
                }
            },
            "required": ["average_high", "average_low", "average_rain_chance", "overall_recommendation"],
            "additionalProperties": False
        },
        "packing_suggestions": {
            "type": "array",
            "description": "Weather-appropriate packing suggestions",
            "items": {"type": "string"}
        }
    },
    "required": ["daily_forecast", "summary", "packing_suggestions"],
    "additionalProperties": False
}


# ============================================================================
# Flight Search Schema
# ============================================================================

FLIGHT_SEARCH_SCHEMA = {
    "type": "object",
    "properties": {
        "flights": {
            "type": "array",
            "description": "List of flight options found",
            "items": {
                "type": "object",
                "properties": {
                    "airline": {
                        "type": "string",
                        "description": "Airline name (e.g., 'Singapore Airlines', 'ANA', 'Delta')"
                    },
                    "flight_number": {
                        "type": "string",
                        "description": "Flight number if found (e.g., 'SQ123'), or 'TBD' if unknown"
                    },
                    "departure_time": {
                        "type": "string",
                        "description": "Departure time in HH:MM format (e.g., '09:30')"
                    },
                    "arrival_time": {
                        "type": "string",
                        "description": "Arrival time in HH:MM format"
                    },
                    "duration": {
                        "type": "string",
                        "description": "Flight duration (e.g., '7h 30m')"
                    },
                    "stops": {
                        "type": "integer",
                        "description": "Number of stops (0 for direct, 1+ for layovers)"
                    },
                    "price_usd": {
                        "type": "number",
                        "description": "Price in USD per person"
                    },
                    "cabin_class": {
                        "type": "string",
                        "description": "Cabin class: Economy, Premium Economy, Business, or First"
                    },
                    "source_url": {
                        "type": "string",
                        "description": "Source URL if available, empty string otherwise"
                    }
                },
                "required": ["airline", "flight_number", "departure_time", "arrival_time", "duration", "stops", "price_usd", "cabin_class", "source_url"],
                "additionalProperties": False
            }
        },
        "summary": {
            "type": "object",
            "description": "Summary of flight options",
            "properties": {
                "cheapest_price": {
                    "type": "number",
                    "description": "Lowest price found in USD"
                },
                "typical_duration": {
                    "type": "string",
                    "description": "Typical flight duration for this route"
                },
                "direct_available": {
                    "type": "boolean",
                    "description": "Whether direct flights are available"
                },
                "recommended_airline": {
                    "type": "string",
                    "description": "Best airline for this route based on value/quality"
                }
            },
            "required": ["cheapest_price", "typical_duration", "direct_available", "recommended_airline"],
            "additionalProperties": False
        }
    },
    "required": ["flights", "summary"],
    "additionalProperties": False
}


# ============================================================================
# Hotel Search Schema
# ============================================================================

HOTEL_SEARCH_SCHEMA = {
    "type": "object",
    "properties": {
        "hotels": {
            "type": "array",
            "description": "List of hotel options found",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Hotel name"
                    },
                    "location": {
                        "type": "string",
                        "description": "Area/neighborhood location"
                    },
                    "rating": {
                        "type": "number",
                        "description": "Rating out of 5.0"
                    },
                    "price_per_night_usd": {
                        "type": "number",
                        "description": "Price per night in USD"
                    },
                    "amenities": {
                        "type": "array",
                        "description": "List of amenities (WiFi, Pool, Gym, etc.)",
                        "items": {"type": "string"}
                    },
                    "distance_to_center": {
                        "type": "string",
                        "description": "Distance to city center (e.g., '1.5 km')"
                    },
                    "near_transport": {
                        "type": "boolean",
                        "description": "Whether hotel is near public transport"
                    },
                    "description": {
                        "type": "string",
                        "description": "Brief description of the hotel"
                    },
                    "source_url": {
                        "type": "string",
                        "description": "Source URL if available, empty string otherwise"
                    }
                },
                "required": ["name", "location", "rating", "price_per_night_usd", "amenities", "distance_to_center", "near_transport", "description", "source_url"],
                "additionalProperties": False
            }
        },
        "summary": {
            "type": "object",
            "description": "Summary of hotel options",
            "properties": {
                "price_range": {
                    "type": "string",
                    "description": "Price range found (e.g., '$80-$200/night')"
                },
                "best_value": {
                    "type": "string",
                    "description": "Name of best value hotel"
                },
                "highest_rated": {
                    "type": "string",
                    "description": "Name of highest rated hotel"
                }
            },
            "required": ["price_range", "best_value", "highest_rated"],
            "additionalProperties": False
        }
    },
    "required": ["hotels", "summary"],
    "additionalProperties": False
}


# ============================================================================
# Activity Search Schema
# ============================================================================

ACTIVITY_SEARCH_SCHEMA = {
    "type": "object",
    "properties": {
        "activities": {
            "type": "array",
            "description": "List of activities and attractions found",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Activity/attraction name"
                    },
                    "category": {
                        "type": "string",
                        "description": "Category: Cultural, Food, Nature, Sightseeing, Shopping, Entertainment, Museum, or Adventure"
                    },
                    "description": {
                        "type": "string",
                        "description": "2-3 sentence description of the activity"
                    },
                    "duration": {
                        "type": "string",
                        "description": "Typical duration (e.g., '2-3 hours')"
                    },
                    "price_usd": {
                        "type": "number",
                        "description": "Entry/activity price in USD (0 for free)"
                    },
                    "rating": {
                        "type": "number",
                        "description": "Rating out of 5.0"
                    },
                    "best_time": {
                        "type": "string",
                        "description": "Best time to visit (e.g., 'Early morning', 'Sunset')"
                    },
                    "tips": {
                        "type": "array",
                        "description": "1-2 practical tips for visitors",
                        "items": {"type": "string"}
                    },
                    "source_url": {
                        "type": "string",
                        "description": "Source URL if available, empty string otherwise"
                    }
                },
                "required": ["name", "category", "description", "duration", "price_usd", "rating", "best_time", "tips", "source_url"],
                "additionalProperties": False
            }
        },
        "must_do": {
            "type": "array",
            "description": "Top 3-5 must-do activities",
            "items": {"type": "string"}
        },
        "free_activities": {
            "type": "array",
            "description": "List of free activities",
            "items": {"type": "string"}
        }
    },
    "required": ["activities", "must_do", "free_activities"],
    "additionalProperties": False
}


# ============================================================================
# Restaurant Search Schema
# ============================================================================

# ============================================================================
# Feasibility Analysis Schema
# ============================================================================

FEASIBILITY_ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "is_feasible": {
            "type": "boolean",
            "description": "Whether the plan can reasonably be executed"
        },
        "confidence": {
            "type": "number",
            "description": "Confidence score 0.0-1.0 for the assessment"
        },
        "issues": {
            "type": "array",
            "description": "Critical blockers that prevent execution",
            "items": {"type": "string"}
        },
        "warnings": {
            "type": "array",
            "description": "Concerns that need attention but aren't blockers",
            "items": {"type": "string"}
        },
        "suggestions": {
            "type": "array",
            "description": "Actionable improvements to make the plan better",
            "items": {"type": "string"}
        },
        "schedule_analysis": {
            "type": "object",
            "description": "Analysis of the schedule",
            "properties": {
                "total_days": {"type": "integer", "description": "Number of days in itinerary"},
                "activities_per_day": {"type": "number", "description": "Average activities per day"},
                "estimated_daily_travel_time": {"type": "string", "description": "Estimated travel time per day"},
                "pace_assessment": {"type": "string", "description": "Assessment of pace: relaxed, moderate, busy"},
                "buffer_time": {"type": "string", "description": "Assessment of buffer time: adequate, tight, insufficient"}
            },
            "required": ["total_days", "activities_per_day", "estimated_daily_travel_time", "pace_assessment", "buffer_time"],
            "additionalProperties": False
        }
    },
    "required": ["is_feasible", "confidence", "issues", "warnings", "suggestions", "schedule_analysis"],
    "additionalProperties": False
}


# ============================================================================
# Cost Breakdown Schema
# ============================================================================

COST_BREAKDOWN_SCHEMA = {
    "type": "object",
    "properties": {
        "total_estimated_cost": {
            "type": "number",
            "description": "Total estimated cost in USD"
        },
        "currency": {
            "type": "string",
            "description": "Currency code (USD)"
        },
        "breakdown": {
            "type": "object",
            "description": "Cost breakdown by category",
            "properties": {
                "flights": {"type": "number", "description": "Flight costs"},
                "accommodation": {"type": "number", "description": "Hotel/accommodation costs"},
                "activities": {"type": "number", "description": "Activity/attraction costs"},
                "food": {"type": "number", "description": "Food and dining costs"},
                "local_transport": {"type": "number", "description": "Local transport costs"},
                "miscellaneous": {"type": "number", "description": "Miscellaneous expenses"}
            },
            "required": ["flights", "accommodation", "activities", "food", "local_transport", "miscellaneous"],
            "additionalProperties": False
        },
        "within_budget": {
            "type": "boolean",
            "description": "Whether total is within the stated budget"
        },
        "budget_remaining": {
            "type": "number",
            "description": "Amount remaining from budget (can be negative if over)"
        },
        "cost_saving_tips": {
            "type": "array",
            "description": "Specific actionable tips to save money",
            "items": {"type": "string"}
        }
    },
    "required": ["total_estimated_cost", "currency", "breakdown", "within_budget", "budget_remaining", "cost_saving_tips"],
    "additionalProperties": False
}


# ============================================================================
# Schedule Optimization Schema
# ============================================================================

SCHEDULE_OPTIMIZATION_SCHEMA = {
    "type": "object",
    "properties": {
        "optimized_schedule": {
            "type": "array",
            "description": "Optimized daily schedule",
            "items": {
                "type": "object",
                "properties": {
                    "day": {"type": "integer", "description": "Day number"},
                    "activities": {
                        "type": "array",
                        "description": "Activities for this day",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "Activity name"},
                                "location": {"type": "string", "description": "Location/area"},
                                "suggested_time": {"type": "string", "description": "Suggested time slot (e.g., '09:00-11:00')"}
                            },
                            "required": ["name", "location", "suggested_time"],
                            "additionalProperties": False
                        }
                    },
                    "notes": {"type": "string", "description": "Notes for this day"}
                },
                "required": ["day", "activities", "notes"],
                "additionalProperties": False
            }
        },
        "changes_made": {
            "type": "array",
            "description": "List of optimizations made",
            "items": {"type": "string"}
        },
        "time_saved": {
            "type": "string",
            "description": "Estimated time saved from optimization"
        },
        "efficiency_score": {
            "type": "number",
            "description": "Efficiency score 0.0-1.0"
        }
    },
    "required": ["optimized_schedule", "changes_made", "time_saved", "efficiency_score"],
    "additionalProperties": False
}


# ============================================================================
# Restaurant Search Schema
# ============================================================================

RESTAURANT_SEARCH_SCHEMA = {
    "type": "object",
    "properties": {
        "restaurants": {
            "type": "array",
            "description": "List of restaurant options found",
            "items": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Restaurant name"
                    },
                    "cuisine_type": {
                        "type": "string",
                        "description": "Type of cuisine (e.g., Japanese, Italian, Local Cuisine)"
                    },
                    "area": {
                        "type": "string",
                        "description": "Area/neighborhood location"
                    },
                    "address": {
                        "type": "string",
                        "description": "Full address if available, or area description"
                    },
                    "price_range": {
                        "type": "string",
                        "description": "Price range: $, $$, $$$, or $$$$"
                    },
                    "price_per_person_usd": {
                        "type": "number",
                        "description": "Average price per person in USD"
                    },
                    "rating": {
                        "type": "number",
                        "description": "Rating out of 5.0"
                    },
                    "specialty_dishes": {
                        "type": "array",
                        "description": "2-3 signature/recommended dishes",
                        "items": {"type": "string"}
                    },
                    "opening_hours": {
                        "type": "string",
                        "description": "Opening hours (e.g., '11:00 AM - 10:00 PM')"
                    },
                    "reservation_required": {
                        "type": "boolean",
                        "description": "Whether reservation is recommended/required"
                    },
                    "wait_time": {
                        "type": "string",
                        "description": "Typical wait time (e.g., '15-30 min', 'No wait')"
                    },
                    "description": {
                        "type": "string",
                        "description": "Brief description of the restaurant"
                    },
                    "source_url": {
                        "type": "string",
                        "description": "Source URL if available, empty string otherwise"
                    }
                },
                "required": ["name", "cuisine_type", "area", "address", "price_range", "price_per_person_usd", "rating", "specialty_dishes", "opening_hours", "reservation_required", "wait_time", "description", "source_url"],
                "additionalProperties": False
            }
        },
        "by_meal_type": {
            "type": "object",
            "description": "Restaurants grouped by meal suitability",
            "properties": {
                "breakfast": {
                    "type": "array",
                    "description": "Names of restaurants good for breakfast",
                    "items": {"type": "string"}
                },
                "lunch": {
                    "type": "array",
                    "description": "Names of restaurants good for lunch",
                    "items": {"type": "string"}
                },
                "dinner": {
                    "type": "array",
                    "description": "Names of restaurants good for dinner",
                    "items": {"type": "string"}
                }
            },
            "required": ["breakfast", "lunch", "dinner"],
            "additionalProperties": False
        }
    },
    "required": ["restaurants", "by_meal_type"],
    "additionalProperties": False
}
