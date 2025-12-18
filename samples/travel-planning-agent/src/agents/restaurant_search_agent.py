"""
Restaurant Search Agent
An intelligent agent that searches for restaurants using Tavily API and extracts data using LLM.
"""

from typing import List, Dict, Any, Optional
import json
import re

from ..utils.config import get_config
from ..utils.schemas import get_response_format, RESTAURANT_SEARCH_SCHEMA


def _get_image_util():
    """Lazy import to avoid circular dependency"""
    from ..tools.image_utils import download_and_encode_base64, search_image_for_item, search_images_parallel
    return download_and_encode_base64, search_image_for_item, search_images_parallel


RESTAURANT_AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "tavily_search",
            "description": "Search the web for restaurant information. Use specific queries about restaurants, cuisine types, dining options, food guides.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for finding restaurant information"
                    }
                },
                "required": ["query"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "extract_restaurants",
            "description": "Extract structured restaurant data from all accumulated search results. Call this after gathering enough search content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Brief explanation of why you're extracting now"
                    }
                },
                "required": ["reason"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "finish",
            "description": "Call this when you have sufficient restaurant data (at least 8 restaurants) or have exhausted search options.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["success", "partial", "no_data"],
                        "description": "success: found good data, partial: found some data, no_data: couldn't find restaurant info"
                    },
                    "summary": {
                        "type": "string",
                        "description": "Brief summary of what was found"
                    }
                },
                "required": ["status", "summary"],
                "additionalProperties": False
            }
        }
    }
]


class RestaurantSearchAgent:
    """Intelligent agent for searching restaurants."""

    MAX_TAVILY_CALLS = 15
    DEFAULT_MIN_RESTAURANTS = 12  # Default for 5-day trip

    def __init__(self, config=None):
        self.config = config or get_config()
        self._reset_state()
        self.min_restaurants_required = self.DEFAULT_MIN_RESTAURANTS

    def _reset_state(self):
        self.content_list: List[str] = []
        self.sources: List[str] = []
        self.image_urls: List[str] = []
        self.tavily_call_count = 0
        self.extracted_data: Optional[Dict[str, Any]] = None
        self.messages: List[Dict[str, Any]] = []

    def search(
        self,
        destination: str,
        areas: Optional[List[str]] = None,
        cuisine_types: Optional[List[str]] = None,
        meal_type: Optional[str] = None,
        num_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """Search for restaurants using the agent."""
        self._reset_state()

        # Calculate minimum restaurants based on trip duration
        # For 3 meals per day, we need at least num_days * 2 unique restaurants
        # (allowing some flexibility for hotel breakfasts, etc.)
        if num_days:
            self.min_restaurants_required = max(num_days * 2, 8)
        else:
            self.min_restaurants_required = self.DEFAULT_MIN_RESTAURANTS

        print(f"  RestaurantSearchAgent: Searching restaurants in {destination} (min: {self.min_restaurants_required})")

        areas_str = ", ".join(areas) if areas else "various areas"
        cuisine_str = ", ".join(cuisine_types) if cuisine_types else "local and international cuisine"

        min_req = self.min_restaurants_required
        system_prompt = f"""You are a restaurant search agent. Find FAMOUS and HIGHLY-RATED dining options at a destination.

## Strategy
1. Start with "best restaurants", "must-try restaurants", "famous local food"
2. Search for award-winning restaurants, Michelin guide recommendations
3. Search for iconic local cuisine spots that travelers should not miss
4. Search for different cuisine types (local, Japanese, international)
5. Extract data after 2-3 searches, if < {min_req} restaurants, do more searches
6. Search specific categories: breakfast spots, lunch cafes, dinner restaurants
7. Call finish when you have at least {min_req} diverse, FAMOUS restaurants

## Success Criteria
- At least {min_req} restaurants (travelers need variety for their trip)
- Focus on FAMOUS, WELL-REVIEWED restaurants worth traveling to try
- Include iconic local specialties and popular tourist favorites
- Mix of breakfast, lunch, and dinner suitable restaurants
- Include price variety: budget-friendly, mid-range, and fine dining"""

        user_prompt = f"""Find restaurant options:

**Destination**: {destination}
**Areas**: {areas_str}
**Cuisines**: {cuisine_str}
**Meal type**: {meal_type or "all meals"}

Search for restaurants, dining options, and food recommendations."""

        self.messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        # Agent loop
        max_iterations = 20
        for iteration in range(max_iterations):
            if self.tavily_call_count >= self.MAX_TAVILY_CALLS:
                if self.content_list and not self.extracted_data:
                    self._execute_extract("Max Tavily calls reached")
                break

            response = self._call_llm()
            if not response:
                break

            tool_calls = response.choices[0].message.tool_calls
            if not tool_calls:
                break

            self.messages.append(response.choices[0].message)

            should_finish = False
            for tool_call in tool_calls:
                result, finished = self._execute_tool(tool_call, destination)
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                })
                if finished:
                    should_finish = True

            if should_finish:
                break

        return self.extracted_data or {"restaurants": [], "by_meal_type": {"breakfast": [], "lunch": [], "dinner": []}}

    def _call_llm(self) -> Any:
        try:
            client = self.config.get_llm_client(label="restaurant_search")
            return client.chat.completions.create(
                model=self.config.llm.model,
                messages=self.messages,
                tools=RESTAURANT_AGENT_TOOLS,
                tool_choice="auto",
                temperature=0.3,
                max_tokens=1000
            )
        except Exception as e:
            print(f"  Agent LLM call failed: {str(e)}")
            return None

    def _execute_tool(self, tool_call: Any, destination: str) -> tuple[Dict[str, Any], bool]:
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        if name == "tavily_search":
            return self._execute_tavily_search(args.get("query", "")), False
        elif name == "extract_restaurants":
            return self._execute_extract(args.get("reason", "")), False
        elif name == "finish":
            print(f"  Agent finished: {args.get('status')} - {args.get('summary')}")
            return {"status": args.get("status"), "summary": args.get("summary")}, True
        return {"error": f"Unknown tool: {name}"}, False

    def _execute_tavily_search(self, query: str) -> Dict[str, Any]:
        if self.tavily_call_count >= self.MAX_TAVILY_CALLS:
            return {"error": "Max Tavily calls reached", "suggestion": "Call extract_restaurants then finish"}

        try:
            from tavily import TavilyClient
            client = TavilyClient(api_key=self.config.search.tavily_api_key)
            self.tavily_call_count += 1

            print(f"  Agent Tavily search ({self.tavily_call_count}/{self.MAX_TAVILY_CALLS}): {query[:50]}...")

            response = client.search(query=query, max_results=5, search_depth="basic", include_images=True)

            results_found = 0
            for img in response.get("images", []):
                url = img if isinstance(img, str) else img.get("url", "")
                if url:
                    self.image_urls.append(url)

            for result in response.get("results", []):
                if result.get("content"):
                    self.content_list.append(result["content"])
                    results_found += 1
                if result.get("url") and result["url"] not in self.sources:
                    self.sources.append(result["url"])

            return {
                "success": True,
                "results_found": results_found,
                "total_content_pieces": len(self.content_list),
                "tavily_calls_remaining": self.MAX_TAVILY_CALLS - self.tavily_call_count
            }
        except Exception as e:
            return {"error": str(e)}

    def _execute_extract(self, reason: str) -> Dict[str, Any]:
        if not self.content_list:
            return {"error": "No search content", "suggestion": "Run tavily_search first"}

        print(f"  Agent extracting restaurants: {reason}")

        try:
            system_prompt = """You are a restaurant data extraction assistant. Extract ALL restaurant information from search results.

## CRITICAL: Extract as many restaurants as possible (aim for 10-15+ per extraction)

## Guidelines
1. Extract EVERY restaurant name mentioned, even if details are partial
2. Prices in USD per person (estimate if not explicit)
3. Ratings out of 5.0 (estimate 4.0 if not given)
4. Include specialty dishes and opening hours when available
5. Categorize by meal suitability (breakfast, lunch, dinner)
6. Don't skip restaurants just because some info is missing - include them anyway"""

            truncated = []
            total_chars = 0
            for content in self.content_list[:15]:
                if total_chars + len(content) > 10000:
                    break
                truncated.append(content)
                total_chars += len(content)

            user_content = f"""## Search Results ({len(truncated)} pieces)

```json
{json.dumps(truncated, indent=2)}
```

## Sources
{json.dumps(self.sources[:10], indent=2)}

## Task
Extract ALL restaurants mentioned (aim for 10-15+). Include names, cuisine types, prices, ratings, and specialty dishes.
For missing info: estimate price range based on cuisine type, use 4.0 rating if unknown."""

            client = self.config.get_llm_client(label="restaurant_extraction")

            try:
                response = client.chat.completions.create(
                    model=self.config.llm.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ],
                    response_format=get_response_format("restaurant_search", RESTAURANT_SEARCH_SCHEMA),
                    temperature=0.2,
                    max_tokens=4000,  # Increased for more restaurants
                )
            except Exception as e:
                if "response_format" in str(e).lower():
                    response = client.chat.completions.create(
                        model=self.config.llm.model,
                        messages=[
                            {"role": "system", "content": system_prompt + "\n\nReturn valid JSON."},
                            {"role": "user", "content": user_content},
                        ],
                        temperature=0.2,
                        max_tokens=4000,  # Increased for more restaurants
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

            for restaurant in data.get("restaurants", []):
                if not restaurant.get("source_url") and self.sources:
                    restaurant["source_url"] = self.sources[0]

            # Add image suggestions
            self._add_image_suggestions(data.get("restaurants", []))

            # Accumulate restaurants across extractions (don't overwrite)
            if self.extracted_data is None:
                self.extracted_data = {"restaurants": [], "by_meal_type": {"breakfast": [], "lunch": [], "dinner": []}}

            # Merge new restaurants, avoiding duplicates by name
            existing_names = {r.get("name", "").lower() for r in self.extracted_data.get("restaurants", [])}
            for restaurant in data.get("restaurants", []):
                name = restaurant.get("name", "").lower()
                if name and name not in existing_names:
                    self.extracted_data["restaurants"].append(restaurant)
                    existing_names.add(name)

            # Merge by_meal_type if present
            for meal_type in ["breakfast", "lunch", "dinner"]:
                existing = self.extracted_data.get("by_meal_type", {}).get(meal_type, [])
                new_meals = data.get("by_meal_type", {}).get(meal_type, [])
                self.extracted_data["by_meal_type"][meal_type] = list(set(existing + new_meals))

            restaurants_count = len(self.extracted_data.get("restaurants", []))

            print(f"  Extracted {restaurants_count} restaurants")

            # Count cuisine types
            cuisines = set(r.get("cuisine_type", "") for r in data.get("restaurants", []))

            return {
                "success": True,
                "restaurants_found": restaurants_count,
                "cuisine_types_found": len(cuisines),
                "cuisines": list(cuisines),
                "data_quality": "good" if restaurants_count >= self.min_restaurants_required else "needs_more",
                "suggestion": (
                    "Data looks good! Call finish with status='success'"
                    if restaurants_count >= self.min_restaurants_required
                    else f"Only {restaurants_count} restaurants. Consider more cuisine-specific searches."
                )
            }
        except Exception as e:
            print(f"  Extraction failed: {str(e)}")
            return {"error": str(e)}

    def _add_image_suggestions(self, restaurants: List[Dict[str, Any]]) -> None:
        """Add image suggestion keys for ImageAgent"""
        for restaurant in restaurants:
            name = restaurant.get("name", "")
            key = re.sub(r'[^a-z0-9\s]', '', name.lower())
            key = re.sub(r'\s+', '_', key.strip())
            if key:
                restaurant["image_suggestion"] = key


class RestaurantSearchTool:
    """Restaurant search tool using the RestaurantSearchAgent."""

    _cache: Dict[str, Dict[str, Any]] = {}

    def __init__(self):
        self.config = get_config()
        if not self.config.search.tavily_api_key:
            raise ValueError("TAVILY_API_KEY is required for restaurant search")
        print("RestaurantSearchTool initialized with RestaurantSearchAgent")
        self.agent = RestaurantSearchAgent(self.config)

    def search_restaurants(
        self,
        destination: str,
        areas: Optional[List[str]] = None,
        cuisine_types: Optional[List[str]] = None,
        meal_type: Optional[str] = None,
        max_budget: Optional[float] = None,
        num_days: Optional[int] = None
    ) -> Dict[str, Any]:
        cache_key = f"{destination.lower()}_{meal_type or 'all'}"

        if cache_key in RestaurantSearchTool._cache:
            print(f"Cache hit for restaurants in {destination}")
            return self._apply_filters(RestaurantSearchTool._cache[cache_key], areas, max_budget)

        print(f"Searching restaurants in {destination} via Agent...")

        result = self.agent.search(destination, areas, cuisine_types, meal_type, num_days)

        # Download images for restaurants using item-specific search
        self._assign_images(result.get("restaurants", []), destination)

        RestaurantSearchTool._cache[cache_key] = result
        return self._apply_filters(result, areas, max_budget)

    def _assign_images(self, restaurants: List[Dict[str, Any]], destination: str) -> None:
        """Assign images to restaurants using parallel Tavily searches."""
        _, _, search_images_parallel_fn = _get_image_util()

        # Use parallel image search for better performance
        image_results = search_images_parallel_fn(
            items=restaurants,
            destination=destination,
            tavily_api_key=self.config.search.tavily_api_key,
            item_type="restaurant",
            max_workers=5
        )

        # Assign results back to restaurants
        for restaurant in restaurants:
            name = restaurant.get("name", "")
            if name and name in image_results and image_results[name]:
                restaurant["image_base64"] = image_results[name]

    def _apply_filters(
        self,
        result: Dict[str, Any],
        areas: Optional[List[str]],
        max_budget: Optional[float]
    ) -> Dict[str, Any]:
        restaurants = result.get("restaurants", []).copy()

        if max_budget:
            restaurants = [r for r in restaurants if r.get("price_per_person_usd", 0) <= max_budget]

        by_area = {}
        for r in restaurants:
            area = r.get("area", "Other")
            if area not in by_area:
                by_area[area] = []
            by_area[area].append(r)

        by_meal = result.get("by_meal_type", {})
        breakfast_names = by_meal.get("breakfast", [])
        lunch_names = by_meal.get("lunch", [])
        dinner_names = by_meal.get("dinner", [])

        breakfast_options = [r for r in restaurants if r.get("name") in breakfast_names or r.get("price_per_person_usd", 0) < 20]
        lunch_options = [r for r in restaurants if r.get("name") in lunch_names or r.get("price_per_person_usd", 0) < 40]
        dinner_options = [r for r in restaurants if r.get("name") in dinner_names or True]

        return {
            "restaurants": restaurants,
            "by_area": by_area,
            "breakfast_options": breakfast_options[:5],
            "lunch_options": lunch_options[:8],
            "dinner_options": dinner_options[:8],
            "budget_friendly": [r for r in restaurants if r.get("price_range") == "$"][:5],
            "fine_dining": [r for r in restaurants if r.get("price_range") in ["$$$", "$$$$"]][:3],
            "total_options": len(restaurants)
        }
