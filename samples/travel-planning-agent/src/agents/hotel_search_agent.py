"""
Hotel Search Agent
An intelligent agent that searches for hotels using Tavily API and extracts data using LLM.
"""

from typing import List, Dict, Any, Optional
import json

from ..utils.config import get_config
from ..utils.schemas import get_response_format, HOTEL_SEARCH_SCHEMA


def _get_image_util():
    """Lazy import to avoid circular dependency"""
    from ..tools.image_utils import download_and_encode_base64
    return download_and_encode_base64


HOTEL_AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "tavily_search",
            "description": "Search the web for hotel information. Use specific queries about hotels, prices, locations, amenities, ratings.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for finding hotel information"
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
            "name": "extract_hotels",
            "description": "Extract structured hotel data from all accumulated search results. Call this after gathering enough search content.",
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
            "description": "Call this when you have sufficient hotel data (at least 5 hotels with prices) or have exhausted search options.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["success", "partial", "no_data"],
                        "description": "success: found good data, partial: found some data, no_data: couldn't find hotel info"
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


class HotelSearchAgent:
    """Intelligent agent for searching hotels."""

    MAX_TAVILY_CALLS = 15
    MIN_HOTELS_REQUIRED = 5

    def __init__(self, config=None):
        self.config = config or get_config()
        self._reset_state()

    def _reset_state(self):
        self.content_list: List[str] = []
        self.sources: List[str] = []
        self.image_urls: List[str] = []
        self.tavily_call_count = 0
        self.extracted_data: Optional[Dict[str, Any]] = None
        self.messages: List[Dict[str, Any]] = []

    def search(self, destination: str, check_in: str, check_out: str) -> Dict[str, Any]:
        """Search for hotels using the agent."""
        self._reset_state()

        print(f"  HotelSearchAgent: Searching hotels in {destination}")

        system_prompt = """You are a hotel search agent. Find hotel options for a destination.

## Strategy
1. Start with a general search for hotels in the destination
2. If results lack prices or variety, search for budget hotels or specific areas
3. Extract data after 2-3 searches to check quality
4. If extraction shows insufficient data (<5 hotels), do more targeted searches
5. Call finish when you have at least 5 hotels with prices

## Success Criteria
- At least 5 hotel options with names and prices in USD
- Mix of budget and mid-range options if available
- Include hotels near public transport"""

        user_prompt = f"""Find hotel options:

**Destination**: {destination}
**Check-in**: {check_in}
**Check-out**: {check_out}

Search for available hotels with prices, ratings, and locations."""

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

        return self.extracted_data or {"hotels": [], "summary": {}}

    def _call_llm(self) -> Any:
        try:
            client = self.config.get_llm_client(label="hotel_search")
            return client.chat.completions.create(
                model=self.config.llm.model,
                messages=self.messages,
                tools=HOTEL_AGENT_TOOLS,
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
        elif name == "extract_hotels":
            return self._execute_extract(args.get("reason", "")), False
        elif name == "finish":
            print(f"  Agent finished: {args.get('status')} - {args.get('summary')}")
            return {"status": args.get("status"), "summary": args.get("summary")}, True
        return {"error": f"Unknown tool: {name}"}, False

    def _execute_tavily_search(self, query: str) -> Dict[str, Any]:
        if self.tavily_call_count >= self.MAX_TAVILY_CALLS:
            return {"error": "Max Tavily calls reached", "suggestion": "Call extract_hotels then finish"}

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

        print(f"  Agent extracting hotels: {reason}")

        try:
            system_prompt = """You are a hotel data extraction assistant. Extract hotel information from search results.

## Guidelines
1. Extract real hotel names, ratings, prices, and amenities
2. Prices should be in USD per night
3. Ratings out of 5.0
4. Mark hotels as near_transport if they mention station, metro, or convenient location"""

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
Extract all hotel options. Include names, prices, ratings, amenities, and locations."""

            client = self.config.get_llm_client(label="hotel_extraction")

            try:
                response = client.chat.completions.create(
                    model=self.config.llm.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ],
                    response_format=get_response_format("hotel_search", HOTEL_SEARCH_SCHEMA),
                    temperature=0.2,
                    max_tokens=2500,
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
                        max_tokens=2500,
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

            for hotel in data.get("hotels", []):
                if not hotel.get("source_url") and self.sources:
                    hotel["source_url"] = self.sources[0]

            self.extracted_data = data
            hotels_count = len(data.get("hotels", []))
            hotels_with_prices = sum(1 for h in data.get("hotels", []) if h.get("price_per_night_usd", 0) > 0)

            print(f"  Extracted {hotels_count} hotel options")

            return {
                "success": True,
                "hotels_found": hotels_count,
                "hotels_with_prices": hotels_with_prices,
                "data_quality": "good" if hotels_with_prices >= self.MIN_HOTELS_REQUIRED else "needs_more",
                "suggestion": (
                    "Data looks good! Call finish with status='success'"
                    if hotels_with_prices >= self.MIN_HOTELS_REQUIRED
                    else f"Only {hotels_with_prices} hotels with prices. Consider more searches."
                )
            }
        except Exception as e:
            print(f"  Extraction failed: {str(e)}")
            return {"error": str(e)}


class HotelSearchTool:
    """Hotel search tool using the HotelSearchAgent."""

    _cache: Dict[tuple, Dict[str, Any]] = {}

    def __init__(self):
        self.config = get_config()
        if not self.config.search.tavily_api_key:
            raise ValueError("TAVILY_API_KEY is required for hotel search")
        print("HotelSearchTool initialized with HotelSearchAgent")
        self.agent = HotelSearchAgent(self.config)

    def search_hotels(
        self,
        destination: str,
        check_in: str,
        check_out: str,
        max_budget_per_night: Optional[float] = None,
        prefer_near_transport: bool = True,
        min_rating: float = 3.5
    ) -> Dict[str, Any]:
        cache_key = (destination.lower(), check_in, check_out)

        if cache_key in HotelSearchTool._cache:
            print(f"Cache hit for hotels in {destination}")
            return self._apply_filters(HotelSearchTool._cache[cache_key], max_budget_per_night, prefer_near_transport, min_rating)

        print(f"Searching hotels in {destination} ({check_in} to {check_out}) via Agent...")

        result = self.agent.search(destination, check_in, check_out)

        # Download images for hotels
        self._assign_images(result.get("hotels", []))

        HotelSearchTool._cache[cache_key] = result
        return self._apply_filters(result, max_budget_per_night, prefer_near_transport, min_rating)

    def _assign_images(self, hotels: List[Dict[str, Any]]) -> None:
        download_fn = _get_image_util()
        for i, hotel in enumerate(hotels):
            if i < len(self.agent.image_urls):
                image_url = self.agent.image_urls[i]
                hotel["image_url"] = image_url
                print(f"  Downloading image for {hotel.get('name', 'hotel')}...")
                hotel["image_base64"] = download_fn(image_url)

    def _apply_filters(
        self,
        result: Dict[str, Any],
        max_budget: Optional[float],
        prefer_near_transport: bool,
        min_rating: float
    ) -> Dict[str, Any]:
        hotels = result.get("hotels", []).copy()

        if max_budget:
            hotels = [h for h in hotels if h.get("price_per_night_usd", 0) <= max_budget]
        hotels = [h for h in hotels if h.get("rating", 0) >= min_rating]

        if prefer_near_transport:
            hotels.sort(key=lambda x: (not x.get("near_transport", False), -x.get("rating", 0), x.get("price_per_night_usd", 9999)))
        else:
            hotels.sort(key=lambda x: (-x.get("rating", 0), x.get("price_per_night_usd", 9999)))

        best_value = None
        highest_rated = None
        if hotels:
            best_value = min(hotels, key=lambda x: x.get("price_per_night_usd", 9999) / max(x.get("rating", 1), 1))
            highest_rated = max(hotels, key=lambda x: x.get("rating", 0))

        return {
            "hotels": hotels[:8],
            "best_value": best_value,
            "highest_rated": highest_rated,
            "summary": result.get("summary", {}),
            "total_options": len(hotels),
            "filters_applied": {
                "max_budget": max_budget,
                "min_rating": min_rating,
                "near_transport": prefer_near_transport
            }
        }
