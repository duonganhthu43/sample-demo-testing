"""
Weather Service Tool
Provides weather forecasts with mock data support
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import random


@dataclass
class WeatherForecast:
    """Weather forecast data structure"""
    date: str
    condition: str
    high_temp: int
    low_temp: int
    precipitation_chance: int
    humidity: int
    recommendation: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "date": self.date,
            "condition": self.condition,
            "high_temp_celsius": self.high_temp,
            "low_temp_celsius": self.low_temp,
            "precipitation_chance": self.precipitation_chance,
            "humidity": self.humidity,
            "recommendation": self.recommendation
        }


class WeatherService:
    """
    Weather service with mock data support
    """

    # In-memory cache
    _cache: Dict[tuple, List[WeatherForecast]] = {}

    # Seasonal weather patterns by region
    WEATHER_PATTERNS = {
        "tokyo": {
            "spring": {"temp_range": (12, 22), "conditions": ["Sunny", "Partly Cloudy", "Cloudy", "Light Rain"], "rain_chance": 30},
            "summer": {"temp_range": (25, 35), "conditions": ["Sunny", "Hot", "Humid", "Thunderstorms"], "rain_chance": 40},
            "autumn": {"temp_range": (15, 25), "conditions": ["Sunny", "Clear", "Partly Cloudy"], "rain_chance": 20},
            "winter": {"temp_range": (2, 12), "conditions": ["Clear", "Cold", "Cloudy"], "rain_chance": 15}
        },
        "default": {
            "spring": {"temp_range": (15, 25), "conditions": ["Sunny", "Partly Cloudy", "Light Rain"], "rain_chance": 25},
            "summer": {"temp_range": (22, 32), "conditions": ["Sunny", "Hot", "Thunderstorms"], "rain_chance": 35},
            "autumn": {"temp_range": (12, 22), "conditions": ["Clear", "Partly Cloudy", "Cloudy"], "rain_chance": 25},
            "winter": {"temp_range": (5, 15), "conditions": ["Clear", "Cold", "Cloudy", "Rain"], "rain_chance": 30}
        }
    }

    PACKING_RECOMMENDATIONS = {
        "Sunny": "Sunscreen, sunglasses, light clothing",
        "Hot": "Light breathable clothing, stay hydrated, portable fan",
        "Humid": "Light, moisture-wicking clothes, small towel",
        "Clear": "Layered clothing for temperature changes",
        "Partly Cloudy": "Light jacket, umbrella just in case",
        "Cloudy": "Light jacket, umbrella recommended",
        "Light Rain": "Umbrella essential, waterproof jacket",
        "Rain": "Umbrella, rain jacket, waterproof shoes",
        "Thunderstorms": "Stay indoors during storms, umbrella, rain gear",
        "Cold": "Warm layers, coat, hat, gloves"
    }

    def __init__(self):
        self.mock_mode = True

    def get_forecast(
        self,
        destination: str,
        start_date: str,
        num_days: int = 7
    ) -> Dict[str, Any]:
        """
        Get weather forecast

        Args:
            destination: City/location
            start_date: Start date (YYYY-MM-DD)
            num_days: Number of days to forecast

        Returns:
            Dictionary with weather forecast
        """
        cache_key = (destination.lower(), start_date, num_days)

        if cache_key in WeatherService._cache:
            print(f"Cache hit for weather in {destination}")
            return self._format_result(WeatherService._cache[cache_key])

        print(f"Getting weather forecast for {destination}")

        # Generate mock forecast
        forecasts = self._generate_mock_forecast(destination, start_date, num_days)
        WeatherService._cache[cache_key] = forecasts

        return self._format_result(forecasts)

    def _generate_mock_forecast(
        self,
        destination: str,
        start_date: str,
        num_days: int
    ) -> List[WeatherForecast]:
        """Generate mock weather forecast"""
        dest_lower = destination.lower()

        # Determine season from date
        month = int(start_date.split("-")[1])
        season = self._get_season(month)

        # Get weather pattern
        if "tokyo" in dest_lower:
            pattern = self.WEATHER_PATTERNS["tokyo"][season]
        else:
            pattern = self.WEATHER_PATTERNS["default"][season]

        forecasts = []
        year, month, day = map(int, start_date.split("-"))

        for i in range(num_days):
            # Calculate date
            current_day = day + i
            # Simple date calculation (not accounting for month boundaries properly)
            date_str = f"{year}-{month:02d}-{min(current_day, 28):02d}"

            # Generate weather
            condition = random.choice(pattern["conditions"])
            temp_low = pattern["temp_range"][0] + random.randint(-3, 3)
            temp_high = pattern["temp_range"][1] + random.randint(-3, 3)
            rain_chance = pattern["rain_chance"] + random.randint(-10, 10)

            # Get recommendation
            recommendation = self.PACKING_RECOMMENDATIONS.get(
                condition,
                "Check local weather updates"
            )

            forecasts.append(WeatherForecast(
                date=date_str,
                condition=condition,
                high_temp=temp_high,
                low_temp=temp_low,
                precipitation_chance=max(0, min(100, rain_chance)),
                humidity=random.randint(50, 80),
                recommendation=recommendation
            ))

        return forecasts

    def _get_season(self, month: int) -> str:
        """Determine season from month (Northern Hemisphere)"""
        if month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        elif month in [9, 10, 11]:
            return "autumn"
        else:
            return "winter"

    def _format_result(self, forecasts: List[WeatherForecast]) -> Dict[str, Any]:
        """Format forecast results"""
        # Calculate averages
        avg_high = sum(f.high_temp for f in forecasts) / len(forecasts)
        avg_low = sum(f.low_temp for f in forecasts) / len(forecasts)
        avg_rain = sum(f.precipitation_chance for f in forecasts) / len(forecasts)

        # Collect unique packing items
        packing_items = set()
        for f in forecasts:
            items = f.recommendation.split(", ")
            packing_items.update(items)

        # Overall recommendation
        if avg_rain > 50:
            overall = "Expect rain - pack waterproof gear"
        elif avg_high > 30:
            overall = "Hot weather expected - pack light, stay hydrated"
        elif avg_low < 10:
            overall = "Cold weather expected - pack warm layers"
        else:
            overall = "Pleasant weather expected - pack layers for comfort"

        return {
            "daily_forecast": [f.to_dict() for f in forecasts],
            "summary": {
                "average_high": round(avg_high, 1),
                "average_low": round(avg_low, 1),
                "average_rain_chance": round(avg_rain, 1),
                "overall_recommendation": overall
            },
            "packing_suggestions": list(packing_items),
            "num_days": len(forecasts)
        }
