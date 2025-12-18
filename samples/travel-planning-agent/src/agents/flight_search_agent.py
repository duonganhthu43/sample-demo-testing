"""
Flight Search Agent
An intelligent agent that searches for flights using Tavily API and extracts data using LLM.
The agent can decide what to search, when to extract, and validate data sufficiency.
"""

from typing import List, Dict, Any, Optional
import json

from ..utils.config import get_config
from ..utils.schemas import get_response_format, FLIGHT_SEARCH_SCHEMA


# Tool definitions for the agent
FLIGHT_AGENT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "tavily_search",
            "description": "Search the web for flight information using Tavily. Use specific queries about airlines, prices, routes, schedules. Returns search results content and source URLs.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for finding flight information. Be specific about route, dates, airlines, or prices."
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
            "name": "extract_flights",
            "description": "Extract structured flight data from all accumulated search results. Call this when you have gathered enough search content (at least 2-3 searches) or want to check if current data is sufficient.",
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
            "description": "Call this when you have sufficient flight data (at least 3 flights with prices) or have exhausted search options.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["success", "partial", "no_data"],
                        "description": "success: found good data, partial: found some data, no_data: couldn't find flight info"
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


class FlightSearchAgent:
    """
    An intelligent agent for searching flights.

    The agent has access to:
    - tavily_search: Search for flight information
    - extract_flights: Extract structured data from search results
    - finish: Complete the search with final results

    The agent decides:
    - What queries to run (adapts based on results)
    - When to extract data
    - Whether data is sufficient or needs more searching
    """

    MAX_TAVILY_CALLS = 20
    MIN_FLIGHTS_REQUIRED = 3

    def __init__(self, config=None):
        self.config = config or get_config()
        self._reset_state()

    def _reset_state(self):
        """Reset agent state for a new search"""
        self.content_list: List[str] = []
        self.sources: List[str] = []
        self.tavily_call_count = 0
        self.extracted_data: Optional[Dict[str, Any]] = None
        self.messages: List[Dict[str, Any]] = []

    def search(
        self,
        origin: str,
        destination: str,
        date: str
    ) -> Dict[str, Any]:
        """
        Search for flights using the agent.

        Args:
            origin: Departure city/airport
            destination: Arrival city/airport
            date: Travel date (YYYY-MM-DD)

        Returns:
            Dictionary with flights and summary
        """
        self._reset_state()

        print(f"  FlightSearchAgent: Searching {origin} -> {destination} on {date}")

        # Initialize conversation with the search task
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(origin, destination, date)

        self.messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        # Agent loop
        max_iterations = 25  # Safety limit
        iteration = 0

        while iteration < max_iterations:
            iteration += 1

            # Check if we've hit Tavily limit
            if self.tavily_call_count >= self.MAX_TAVILY_CALLS:
                print(f"  Agent: Reached max Tavily calls ({self.MAX_TAVILY_CALLS})")
                # Force extraction if we have content
                if self.content_list and not self.extracted_data:
                    self._execute_extract_flights("Max Tavily calls reached")
                break

            # Get next action from LLM
            response = self._call_llm()

            if not response:
                break

            # Check for tool calls
            tool_calls = response.choices[0].message.tool_calls

            if not tool_calls:
                # No tool calls - agent is done or confused
                content = response.choices[0].message.content
                if content:
                    print(f"  Agent message: {content[:100]}...")
                break

            # Add assistant message to history
            self.messages.append(response.choices[0].message)

            # Process tool calls
            should_finish = False
            for tool_call in tool_calls:
                result, finished = self._execute_tool(tool_call, origin, destination, date)

                # Add tool result to messages
                self.messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result)
                })

                if finished:
                    should_finish = True

            if should_finish:
                break

        # Return final result
        if self.extracted_data:
            return self.extracted_data
        else:
            return {"flights": [], "summary": {}}

    def _build_system_prompt(self) -> str:
        return """You are a flight search agent. Your goal is to find flight options for a specific route.

## Strategy
1. Start with a general search about the route (include airline names, prices, schedules)
2. If initial results lack schedule details, search for specific airline schedules
3. Extract data after 2-3 searches to check quality
4. If extraction shows insufficient data (<3 flights with complete info), do more targeted searches
5. Call finish when you have at least 3 flights with prices and times

## Search Tips
- Include "flights schedule", "departure time", "flight times" in queries
- Search for specific airlines on the route: "[airline] [origin] to [destination] schedule"
- Try "[origin] [destination] direct flights departure times"
- Include year (2024/2025) for recent data

## Success Criteria
- At least 3 flight options with airline names, prices, and departure/arrival times
- Mix of direct and connecting options if available
- Prefer results with complete schedule information"""

    def _build_user_prompt(self, origin: str, destination: str, date: str) -> str:
        return f"""Find flight options for this route:

**Origin**: {origin}
**Destination**: {destination}
**Date**: {date}

Search for available flights, prices, and airlines. I need at least 3-5 flight options with prices."""

    def _call_llm(self) -> Any:
        """Call the LLM to get next action"""
        try:
            client = self.config.get_llm_client(label="flight_search")
            response = client.chat.completions.create(
                model=self.config.llm.model,
                messages=self.messages,
                tools=FLIGHT_AGENT_TOOLS,
                tool_choice="auto",
                temperature=0.3,
                max_tokens=1000
            )
            return response
        except Exception as e:
            print(f"  Agent LLM call failed: {str(e)}")
            return None

    def _execute_tool(
        self,
        tool_call: Any,
        origin: str,
        destination: str,
        date: str
    ) -> tuple[Dict[str, Any], bool]:
        """
        Execute a tool call.

        Returns:
            (result_dict, should_finish)
        """
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)

        if name == "tavily_search":
            result = self._execute_tavily_search(args.get("query", ""))
            return result, False

        elif name == "extract_flights":
            result = self._execute_extract_flights(args.get("reason", ""))
            return result, False

        elif name == "finish":
            status = args.get("status", "success")
            summary = args.get("summary", "")
            print(f"  Agent finished: {status} - {summary}")
            return {"status": status, "summary": summary}, True

        else:
            return {"error": f"Unknown tool: {name}"}, False

    def _execute_tavily_search(self, query: str) -> Dict[str, Any]:
        """Execute a Tavily search"""
        if self.tavily_call_count >= self.MAX_TAVILY_CALLS:
            return {
                "error": "Max Tavily calls reached",
                "suggestion": "Call extract_flights to get results from existing data, then finish"
            }

        try:
            from tavily import TavilyClient

            client = TavilyClient(api_key=self.config.search.tavily_api_key)
            self.tavily_call_count += 1

            print(f"  Agent Tavily search ({self.tavily_call_count}/{self.MAX_TAVILY_CALLS}): {query[:50]}...")

            response = client.search(
                query=query,
                max_results=5,
                search_depth="basic"
            )

            results_found = 0
            for result in response.get("results", []):
                content = result.get("content", "")
                url = result.get("url", "")
                if content:
                    self.content_list.append(content)
                    results_found += 1
                if url and url not in self.sources:
                    self.sources.append(url)

            return {
                "success": True,
                "results_found": results_found,
                "total_content_pieces": len(self.content_list),
                "total_sources": len(self.sources),
                "tavily_calls_remaining": self.MAX_TAVILY_CALLS - self.tavily_call_count,
                "hint": "Consider calling extract_flights after 2-3 searches to check data quality"
            }

        except Exception as e:
            print(f"  Tavily search failed: {str(e)}")
            return {
                "error": str(e),
                "tavily_calls_remaining": self.MAX_TAVILY_CALLS - self.tavily_call_count
            }

    def _execute_extract_flights(self, reason: str) -> Dict[str, Any]:
        """Extract flight data from accumulated content"""
        if not self.content_list:
            return {
                "error": "No search content to extract from",
                "suggestion": "Run tavily_search first to gather flight information"
            }

        print(f"  Agent extracting flights: {reason}")

        try:
            # Build extraction prompt
            system_prompt = """You are a flight data extraction assistant. Extract flight information from search results.

## Guidelines
1. Extract real airline names, prices, durations, and times from the search content
2. For flight numbers: use 'TBD' if not explicitly stated
3. Prices should be in USD per person for economy class
4. For departure/arrival times:
   - Use actual times if found in the content
   - If not found, infer realistic times based on typical flight schedules for the route
   - Use format like "08:00", "14:30", "21:15"
   - Do NOT use "TBD" for times - always provide realistic estimates
5. For duration: estimate based on route distance if not stated (e.g., Singapore-Tokyo is ~7h)
6. Mark flights as direct (0 stops) only if explicitly stated or route suggests it
7. Include source URLs when available
8. For airline names:
   - Use the actual airline name if mentioned in the content or URL
   - If source URL contains airline name (e.g., flyscoot.com, ana.co.jp), use that airline
   - If price is from aggregator (Expedia/Skyscanner/Kayak), infer likely airline based on:
     * Route (Singapore-Tokyo: Singapore Airlines, Scoot, ANA, JAL, Jetstar)
     * Price point (budget ~$150-250: Scoot/Jetstar, premium ~$400+: Singapore Airlines/ANA)
   - Do NOT use "TBD" for airline names - always provide a likely airline

The response schema has detailed descriptions for each field - follow those exactly."""

            # Truncate content to avoid token limits
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
Extract all flight options from the search results. Include airline names, prices, durations, and stops."""

            client = self.config.get_llm_client(label="flight_extraction")

            try:
                response = client.chat.completions.create(
                    model=self.config.llm.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content},
                    ],
                    response_format=get_response_format("flight_search", FLIGHT_SEARCH_SCHEMA),
                    temperature=0.2,
                    max_tokens=2000,
                )
            except Exception as e:
                msg = str(e).lower()
                if "response_format" in msg or "unknown" in msg or "unsupported" in msg:
                    response = client.chat.completions.create(
                        model=self.config.llm.model,
                        messages=[
                            {"role": "system", "content": system_prompt + "\n\nReturn your response as valid JSON."},
                            {"role": "user", "content": user_content},
                        ],
                        temperature=0.2,
                        max_tokens=2000,
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

            # Add source URLs to flights
            for flight in data.get("flights", []):
                if not flight.get("source_url") and self.sources:
                    flight["source_url"] = self.sources[0]

            self.extracted_data = data
            flights_count = len(data.get("flights", []))

            print(f"  Extracted {flights_count} flight options")

            # Build feedback for agent
            flights_with_prices = sum(1 for f in data.get("flights", []) if f.get("price_usd", 0) > 0)

            return {
                "success": True,
                "flights_found": flights_count,
                "flights_with_prices": flights_with_prices,
                "has_direct_flights": any(f.get("stops", 1) == 0 for f in data.get("flights", [])),
                "data_quality": "good" if flights_with_prices >= self.MIN_FLIGHTS_REQUIRED else "needs_more",
                "suggestion": (
                    "Data looks good! Call finish with status='success'"
                    if flights_with_prices >= self.MIN_FLIGHTS_REQUIRED
                    else f"Only {flights_with_prices} flights with prices. Consider more searches for price info, then extract again."
                )
            }

        except Exception as e:
            print(f"  Extraction failed: {str(e)}")
            return {
                "error": str(e),
                "suggestion": "Try more searches with different queries"
            }


class FlightSearchTool:
    """
    Flight search tool using the FlightSearchAgent.
    Maintains the same interface as before but uses the intelligent agent internally.
    """

    # In-memory cache (stores extracted flight dicts)
    _cache: Dict[tuple, Dict[str, Any]] = {}

    def __init__(self):
        self.config = get_config()

        if not self.config.search.tavily_api_key:
            raise ValueError("TAVILY_API_KEY is required for flight search")
        print("FlightSearchTool initialized with FlightSearchAgent")

        self.agent = FlightSearchAgent(self.config)

    def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        max_budget: Optional[float] = None,
        prefer_direct: bool = False
    ) -> Dict[str, Any]:
        """
        Search for flights using the intelligent agent.

        Args:
            origin: Departure city/airport
            destination: Arrival city/airport
            departure_date: Departure date (YYYY-MM-DD)
            return_date: Return date for round trip
            max_budget: Maximum budget per person
            prefer_direct: Prefer direct flights

        Returns:
            Dictionary with outbound and return flight options
        """
        cache_key = (origin.lower(), destination.lower(), departure_date, return_date)

        if cache_key in FlightSearchTool._cache:
            print(f"Cache hit for flights: {origin} -> {destination}")
            return self._apply_filters(FlightSearchTool._cache[cache_key], max_budget, prefer_direct)

        print(f"Searching flights: {origin} -> {destination} on {departure_date} via Agent...")

        # Search outbound flights with agent
        outbound_result = self.agent.search(origin, destination, departure_date)

        # Search return flights if needed
        return_result = None
        if return_date:
            return_result = self.agent.search(destination, origin, return_date)

        # Combine results
        result = {
            "outbound_flights": outbound_result.get("flights", []),
            "return_flights": return_result.get("flights", []) if return_result else [],
            "outbound_summary": outbound_result.get("summary", {}),
            "return_summary": return_result.get("summary", {}) if return_result else {},
            "total_options": len(outbound_result.get("flights", [])) + (len(return_result.get("flights", [])) if return_result else 0)
        }

        FlightSearchTool._cache[cache_key] = result
        return self._apply_filters(result, max_budget, prefer_direct)

    def _apply_filters(
        self,
        result: Dict[str, Any],
        max_budget: Optional[float],
        prefer_direct: bool
    ) -> Dict[str, Any]:
        """Apply budget and preference filters to results"""
        filtered = result.copy()

        outbound = filtered.get("outbound_flights", [])
        return_flights = filtered.get("return_flights", [])

        # Apply budget filter
        if max_budget:
            outbound = [f for f in outbound if f.get("price_usd", 0) <= max_budget]
            return_flights = [f for f in return_flights if f.get("price_usd", 0) <= max_budget]

        # Sort by preference
        if prefer_direct:
            outbound.sort(key=lambda x: (x.get("stops", 99), x.get("price_usd", 9999)))
            return_flights.sort(key=lambda x: (x.get("stops", 99), x.get("price_usd", 9999)))
        else:
            outbound.sort(key=lambda x: x.get("price_usd", 9999))
            return_flights.sort(key=lambda x: x.get("price_usd", 9999))

        # Get best options
        best_outbound = outbound[0] if outbound else None
        best_return = return_flights[0] if return_flights else None

        return {
            "outbound_flights": outbound[:5],
            "return_flights": return_flights[:5],
            "best_outbound": best_outbound,
            "best_return": best_return,
            "outbound_summary": filtered.get("outbound_summary", {}),
            "return_summary": filtered.get("return_summary", {}),
            "total_options": len(outbound) + len(return_flights)
        }
