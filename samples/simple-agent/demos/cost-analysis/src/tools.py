"""
Cost Analysis Demo - Tools

Standard tool definitions for the cost analysis demo.
No bugs - just provides search capability.
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

    return {
        "query": query,
        "results": [
            {
                "title": f"Understanding {query}",
                "url": f"https://example.com/{query.replace(' ', '-')}-guide",
                "content": f"Comprehensive guide about {query}. Key insights and analysis.",
                "score": 0.95
            },
            {
                "title": f"{query} - Expert Analysis",
                "url": f"https://example.com/{query.replace(' ', '-')}-analysis",
                "content": f"Expert analysis of {query} with data and trends.",
                "score": 0.90
            }
        ]
    }


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
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
        "web_search": web_search,
    }

    if tool_name not in tools:
        return {"error": f"Unknown tool: {tool_name}"}

    return tools[tool_name](**arguments)
