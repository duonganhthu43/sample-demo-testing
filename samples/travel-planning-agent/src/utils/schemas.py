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
            "items": {
                "type": "object",
                "properties": {
                    "day": {"type": "integer"},
                    "date": {"type": "string"},
                    "theme": {"type": "string"},
                    "schedule": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "time": {"type": "string"},
                                "activity": {"type": "string"},
                                "location": {"type": "string"},
                                "category": {"type": "string"},
                                "notes": {"type": "string"},
                                "cost": {"type": "number"},
                                "source_url": {"type": "string"}
                            },
                            "required": ["time", "activity", "location", "category", "notes", "cost", "source_url"],
                            "additionalProperties": False
                        }
                    },
                    "day_cost": {"type": "number"}
                },
                "required": ["day", "date", "theme", "schedule", "day_cost"],
                "additionalProperties": False
            }
        },
        "total_estimated_cost": {"type": "number"},
        "summary": {"type": "string"},
        "packing_list": {
            "type": "array",
            "items": {"type": "string"}
        },
        "important_notes": {
            "type": "array",
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
        "overview": {"type": "string"},
        "visa_requirements": {"type": "string"},
        "best_time_to_visit": {"type": "string"},
        "language": {"type": "string"},
        "currency": {"type": "string"},
        "time_zone": {"type": "string"},
        "cultural_tips": {
            "type": "array",
            "items": {"type": "string"}
        },
        "safety_rating": {"type": "string"},
        "local_cuisine": {
            "type": "array",
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
            "items": {
                "type": "object",
                "properties": {
                    "date": {"type": "string"},
                    "condition": {"type": "string"},
                    "high_temp_celsius": {"type": "integer"},
                    "low_temp_celsius": {"type": "integer"},
                    "precipitation_chance": {"type": "integer"},
                    "humidity": {"type": "integer"},
                    "recommendation": {"type": "string"}
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
            "properties": {
                "average_high": {"type": "number"},
                "average_low": {"type": "number"},
                "average_rain_chance": {"type": "number"},
                "overall_recommendation": {"type": "string"}
            },
            "required": ["average_high", "average_low", "average_rain_chance", "overall_recommendation"],
            "additionalProperties": False
        },
        "packing_suggestions": {
            "type": "array",
            "items": {"type": "string"}
        }
    },
    "required": ["daily_forecast", "summary", "packing_suggestions"],
    "additionalProperties": False
}
