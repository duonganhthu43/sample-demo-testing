""" 
Weather Service Tool
Provides weather forecasts with mock data support
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import random
import json
from datetime import datetime, timedelta

from ..utils.config import get_config
from ..utils.schemas import get_response_format, WEATHER_FORECAST_SCHEMA


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
        config = get_config()
        self.mock_mode = config.app.mock_external_apis
        self.tavily_api_key = config.search.tavily_api_key
        self.config = config

        if not self.tavily_api_key:
            if self.mock_mode:
                print("Tavily key not found - using mock mode for weather")
            else:
                raise ValueError("TAVILY_API_KEY is required when MOCK_EXTERNAL_APIS=false")

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

        if self.mock_mode and not self.tavily_api_key:
            forecasts = self._generate_mock_forecast(destination, start_date, num_days)
            WeatherService._cache[cache_key] = forecasts
            return self._format_result(forecasts)

        forecast = self._get_forecast_via_tavily(destination, start_date, num_days)
        WeatherService._cache[cache_key] = forecast
        return forecast

    def _get_forecast_via_tavily(self, destination: str, start_date: str, num_days: int) -> Dict[str, Any]:
        content_list, sources = self._search_tavily_weather(destination, start_date, num_days)
        try:
            extracted = self._extract_weather_with_llm(destination, start_date, num_days, content_list)
            extracted["sources"] = sources[:5]
            return extracted
        except Exception as e:
            print(f"Weather extraction failed: {str(e)}")
            if self.mock_mode:
                forecasts = self._generate_mock_forecast(destination, start_date, num_days)
                return self._format_result(forecasts)
            raise

    def _search_tavily_weather(self, destination: str, start_date: str, num_days: int) -> Tuple[List[str], List[str]]:
        try:
            from tavily import TavilyClient

            client = TavilyClient(api_key=self.tavily_api_key)

            content_list: List[str] = []
            sources: List[str] = []

            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            except Exception:
                start_dt = datetime.utcnow()

            end_dt = start_dt + timedelta(days=max(1, num_days))
            date_range = f"{start_dt.strftime('%Y-%m-%d')} to {end_dt.strftime('%Y-%m-%d')}"

            queries = [
                f"{destination} weather forecast {date_range} daily high low precipitation",
                f"{destination} expected weather {date_range} temperature rain humidity",
                f"{destination} climatology typical weather {start_dt.strftime('%B %Y')} high low rain",
            ]

            for query in queries:
                try:
                    print(f"  Tavily query: {query}")
                    response = client.search(
                        query=query,
                        max_results=4,
                        search_depth="basic"
                    )

                    for result in response.get("results", []):
                        content = result.get("content", "")
                        url = result.get("url", "")
                        if content:
                            content_list.append(content)
                        if url and url not in sources:
                            sources.append(url)
                except Exception as e:
                    print(f"  Query failed: {str(e)}")
                    continue

            if not content_list:
                raise ValueError("No Tavily weather results")

            return content_list, sources

        except Exception as e:
            print(f"Tavily weather search failed: {str(e)}")
            raise

    def _extract_weather_with_llm(
        self,
        destination: str,
        start_date: str,
        num_days: int,
        content_list: List[str]
    ) -> Dict[str, Any]:
        system_prompt = """You are a weather data extraction assistant.

Extract a structured travel weather forecast from the provided search snippets.

Return ONLY valid JSON with this schema:
{
  "daily_forecast": [
    {
      "date": "YYYY-MM-DD",
      "condition": "Sunny/Cloudy/Rain/etc",
      "high_temp_celsius": 0,
      "low_temp_celsius": 0,
      "precipitation_chance": 0,
      "humidity": 0,
      "recommendation": "short packing/actionable note"
    }
  ],
  "summary": {
    "average_high": 0,
    "average_low": 0,
    "average_rain_chance": 0,
    "overall_recommendation": "short overall weather summary"
  },
  "packing_suggestions": ["item1", "item2"]
}

Rules:
- daily_forecast MUST have exactly num_days items.
- Use best-effort extraction; if a field isn't present, infer conservatively.
"""

        # Build structured user content for better LLM understanding
        user_content = self._build_weather_content(destination, start_date, num_days, content_list)

        client = self.config.get_llm_client(label="weather_service")
        try:
            response = client.chat.completions.create(
                model=self.config.llm.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": user_content,  # Array of {"type": "text", "text": ...}
                    },
                ],
                response_format=get_response_format("weather_forecast", WEATHER_FORECAST_SCHEMA),
                temperature=0.2,
                max_tokens=1500,
            )
        except Exception as e:
            msg = str(e).lower()
            if "response_format" in msg or "unknown" in msg or "unsupported" in msg:
                response = client.chat.completions.create(
                    model=self.config.llm.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": user_content,
                        },
                    ],
                    temperature=0.2,
                    max_tokens=1500,
                )
            else:
                raise

        content = response.choices[0].message.content or ""
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]

        data = json.loads(content.strip())

        daily = data.get("daily_forecast")
        if not isinstance(daily, list) or len(daily) != num_days:
            raise ValueError("Invalid daily_forecast length")

        return data

    def _build_weather_content(
        self,
        destination: str,
        start_date: str,
        num_days: int,
        content_list: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Build structured content array for weather extraction.

        Returns an array of content parts for better LLM understanding:
        - Separates request parameters from search results
        - Uses JSON for structured data
        """
        content_parts = []

        # Part 1: Request parameters as JSON
        request_data = {
            "destination": destination,
            "start_date": start_date,
            "num_days": num_days
        }
        content_parts.append({
            "type": "text",
            "text": f"## Weather Request\n\n```json\n{json.dumps(request_data, indent=2)}\n```"
        })

        # Part 2: Search results (truncated to avoid token limits)
        truncated_content = []
        total_chars = 0
        for content in content_list[:10]:
            if total_chars + len(content) > 10000:
                break
            truncated_content.append(content)
            total_chars += len(content)

        content_parts.append({
            "type": "text",
            "text": f"## Search Snippets\n\n```json\n{json.dumps(truncated_content, indent=2)}\n```"
        })

        # Part 3: Task instruction
        content_parts.append({
            "type": "text",
            "text": "## Task\n\nExtract weather forecast data from the search snippets above."
        })

        return content_parts

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
