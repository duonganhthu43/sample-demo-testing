"""
Error Detection Demo - Tools with Name Mismatch Bug

BUG: Tool schema defines "search_web" but executor expects "web_search"
This causes "Unknown tool" errors that should be detected by the debug agent.
"""

import os
import requests
from typing import Any


def web_search(query: str) -> dict:
    """Search the web for information."""
    tavily_key = os.getenv("TAVILY_API_KEY")

    if tavily_key and tavily_key.startswith("tvly-"):
        try:
            response = requests.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": tavily_key,
                    "query": query,
                    "search_depth": "basic",
                    "max_results": 3
                },
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[Tools] Tavily search failed: {e}, using mock data")

    # Mock results
    return {
        "query": query,
        "results": [
            {
                "title": f"Understanding {query}",
                "url": f"https://example.com/{query.replace(' ', '-')}-guide",
                "content": f"Comprehensive guide about {query}.",
                "score": 0.95
            },
            {
                "title": f"{query} - Wikipedia",
                "url": f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}",
                "content": f"Wikipedia article about {query}.",
                "score": 0.90
            }
        ]
    }


# =============================================================================
# BUG: Tool name is "search_web" here but function is "web_search"
# =============================================================================
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_web",  # BUG: Doesn't match function name "web_search"
            "description": "Search the web for information on a topic",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query"
                    }
                },
                "required": ["query"]
            }
        }
    }
]


def execute_tool(tool_name: str, arguments: dict) -> Any:
    """Execute a tool by name."""
    tools = {
        "web_search": web_search,  # BUG: LLM calls "search_web" but this expects "web_search"
    }

    if tool_name not in tools:
        return {"error": f"Unknown tool: {tool_name}"}

    return tools[tool_name](**arguments)
