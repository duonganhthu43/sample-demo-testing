"""
Weather Service Tool
Provides weather forecasts using Tavily search and LLM extraction
"""

from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
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
    Weather service using Tavily search and LLM extraction
    """

    # In-memory cache (stores extracted forecast dicts)
    _cache: Dict[tuple, Dict[str, Any]] = {}

    def __init__(self):
        config = get_config()
        self.tavily_api_key = config.search.tavily_api_key
        self.config = config

        if not self.tavily_api_key:
            raise ValueError("TAVILY_API_KEY is required for weather service")
        print("WeatherService initialized with Tavily")

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
            return WeatherService._cache[cache_key]

        print(f"Getting weather forecast for {destination}")

        forecast = self._get_forecast_via_tavily(destination, start_date, num_days)
        WeatherService._cache[cache_key] = forecast
        return forecast

    def _get_forecast_via_tavily(self, destination: str, start_date: str, num_days: int) -> Dict[str, Any]:
        content_list, sources = self._search_tavily_weather(destination, start_date, num_days)
        extracted = self._extract_weather_with_llm(destination, start_date, num_days, content_list)
        extracted["sources"] = sources[:5]
        return extracted

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
        system_prompt = """You are a weather data extraction assistant. Extract weather forecasts from search results.

## Guidelines
1. daily_forecast MUST have exactly the requested number of days
2. Use data from search results; infer conservatively if missing
3. Temperatures in Celsius, precipitation as percentage (0-100)
4. Recommendations should be practical for travelers

The response schema has detailed descriptions for each field - follow those exactly."""

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
