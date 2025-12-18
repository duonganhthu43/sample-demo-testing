"""
Activity Search Agent
An intelligent agent that searches for activities/attractions using Tavily API and extracts data using LLM.
"""

from typing import List, Dict, Any, Optional
import json

from ..utils.config import get_config
from ..utils.schemas import get_response_format, ACTIVITY_SEARCH_SCHEMA


def _get_image_util():
    """Lazy import to avoid circular dependency"""
    from ..tools.image_utils import download_and_encode_base64
    return download_and_encode_base64


ACTIVITY_AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "tavily_search",
            "description": "Search the web for activities and attractions. Use specific queries about things to do, attractions, museums, temples, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for finding activity information"
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
            "name": "extract_activities",
            "description": "Extract structured activity data from all accumulated search results. Call this after gathering enough search content.",
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
            "description": "Call this when you have sufficient activity data (at least 8 activities) or have exhausted search options.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["success", "partial", "no_data"],
                        "description": "success: found good data, partial: found some data, no_data: couldn't find activity info"
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


class ActivitySearchAgent:
    """Intelligent agent for searching activities and attractions."""

    MAX_TAVILY_CALLS = 15
    MIN_ACTIVITIES_REQUIRED = 8

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

    def search(self, destination: str, interests: Optional[List[str]] = None) -> Dict[str, Any]:
        """Search for activities using the agent."""
        self._reset_state()

        print(f"  ActivitySearchAgent: Searching activities in {destination}")

        interests_str = ", ".join(interests) if interests else "general sightseeing, culture, food"

        system_prompt = """You are an activity search agent. Find attractions and things to do at a destination.

## Strategy
1. Start with top attractions and must-see places
2. Search for cultural activities (temples, museums, historic sites)
3. Search for unique local experiences
4. Extract data after 2-3 searches to check variety
5. If lacking categories, search specifically for those (nature, food tours, etc.)
6. Call finish when you have at least 8-10 diverse activities

## Success Criteria
- At least 8 activities covering different categories
- Mix of free and paid activities
- Include iconic landmarks and hidden gems"""

        user_prompt = f"""Find activities and attractions:

**Destination**: {destination}
**Interests**: {interests_str}

Search for things to do, attractions, experiences, and activities."""

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

        return self.extracted_data or {"activities": [], "must_do": [], "free_activities": []}

    def _call_llm(self) -> Any:
        try:
            client = self.config.get_llm_client(label="activity_search_agent")
            return client.chat.completions.create(
                model=self.config.llm.model,
                messages=self.messages,
                tools=ACTIVITY_AGENT_TOOLS,
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
        elif name == "extract_activities":
            return self._execute_extract(args.get("reason", "")), False
        elif name == "finish":
            print(f"  Agent finished: {args.get('status')} - {args.get('summary')}")
            return {"status": args.get("status"), "summary": args.get("summary")}, True
        return {"error": f"Unknown tool: {name}"}, False

    def _execute_tavily_search(self, query: str) -> Dict[str, Any]:
        if self.tavily_call_count >= self.MAX_TAVILY_CALLS:
            return {"error": "Max Tavily calls reached", "suggestion": "Call extract_activities then finish"}

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

        print(f"  Agent extracting activities: {reason}")

        try:
            system_prompt = """You are an activity extraction assistant. Extract tourist activities from search results.

## Guidelines
1. Extract real attraction names, descriptions, and practical details
2. Categories: Cultural, Food, Nature, Sightseeing, Shopping, Entertainment, Museum, Adventure
3. Prices in USD (0 for free attractions)
4. Ratings out of 5.0
5. Include practical tips and best times to visit"""

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
Extract all activities and attractions. Include names, categories, prices, durations, and tips."""

            client = self.config.get_llm_client(label="activity_extraction")

            try:
                response = client.chat.completions.create(
                    model=self.config.llm.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ],
                    response_format=get_response_format("activity_search", ACTIVITY_SEARCH_SCHEMA),
                    temperature=0.2,
                    max_tokens=3000,
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
                        max_tokens=3000,
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

            for activity in data.get("activities", []):
                if not activity.get("source_url") and self.sources:
                    activity["source_url"] = self.sources[0]

            self.extracted_data = data
            activities_count = len(data.get("activities", []))

            print(f"  Extracted {activities_count} activities")

            # Count categories
            categories = set(a.get("category", "") for a in data.get("activities", []))

            return {
                "success": True,
                "activities_found": activities_count,
                "categories_found": len(categories),
                "categories": list(categories),
                "data_quality": "good" if activities_count >= self.MIN_ACTIVITIES_REQUIRED else "needs_more",
                "suggestion": (
                    "Data looks good! Call finish with status='success'"
                    if activities_count >= self.MIN_ACTIVITIES_REQUIRED
                    else f"Only {activities_count} activities. Consider more category-specific searches."
                )
            }
        except Exception as e:
            print(f"  Extraction failed: {str(e)}")
            return {"error": str(e)}


class ActivitySearchTool:
    """Activity search tool using the ActivitySearchAgent."""

    _cache: Dict[tuple, Dict[str, Any]] = {}

    def __init__(self):
        self.config = get_config()
        if not self.config.search.tavily_api_key:
            raise ValueError("TAVILY_API_KEY is required for activity search")
        print("ActivitySearchTool initialized with ActivitySearchAgent")
        self.agent = ActivitySearchAgent(self.config)

    def search_activities(
        self,
        destination: str,
        interests: Optional[List[str]] = None,
        max_budget_per_activity: Optional[float] = None,
        include_free: bool = True
    ) -> Dict[str, Any]:
        cache_key = (destination.lower(), tuple(interests or []))

        if cache_key in ActivitySearchTool._cache:
            print(f"Cache hit for activities in {destination}")
            return self._apply_filters(ActivitySearchTool._cache[cache_key], interests, max_budget_per_activity, include_free)

        print(f"Searching activities in {destination} via Agent...")

        result = self.agent.search(destination, interests)

        # Download images for activities
        self._assign_images(result.get("activities", []))

        ActivitySearchTool._cache[cache_key] = result
        return self._apply_filters(result, interests, max_budget_per_activity, include_free)

    def _assign_images(self, activities: List[Dict[str, Any]]) -> None:
        download_fn = _get_image_util()
        for i, activity in enumerate(activities):
            if i < len(self.agent.image_urls):
                image_url = self.agent.image_urls[i]
                activity["image_url"] = image_url
                print(f"  Downloading image for {activity.get('name', 'activity')}...")
                activity["image_base64"] = download_fn(image_url)

    def _apply_filters(
        self,
        result: Dict[str, Any],
        interests: Optional[List[str]],
        max_budget: Optional[float],
        include_free: bool
    ) -> Dict[str, Any]:
        activities = result.get("activities", []).copy()

        if interests:
            interests_lower = [i.lower() for i in interests]
            filtered = [a for a in activities if a.get("category", "").lower() in interests_lower]
            if filtered:
                activities = filtered

        if max_budget is not None:
            if include_free:
                activities = [a for a in activities if a.get("price_usd", 0) <= max_budget]
            else:
                activities = [a for a in activities if 0 < a.get("price_usd", 0) <= max_budget]

        activities.sort(key=lambda x: -x.get("rating", 0))

        by_category = {}
        for act in activities:
            cat = act.get("category", "Other")
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(act)

        return {
            "activities": activities,
            "by_category": by_category,
            "must_do": result.get("must_do", []),
            "free_activities": result.get("free_activities", []),
            "total_options": len(activities)
        }
