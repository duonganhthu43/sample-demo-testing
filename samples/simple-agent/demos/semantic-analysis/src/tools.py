"""
Semantic Analysis Demo - Standard Tools

No bugs in tools - the issue is in the system prompt.
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
                "content": f"Comprehensive guide about {query}.",
                "score": 0.95
            }
        ]
    }


def save_note(note: str) -> dict:
    """Save a research note."""
    return {"status": "saved", "note": note[:100]}


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
    },
    {
        "type": "function",
        "function": {
            "name": "save_note",
            "description": "Save a research note for later reference",
            "parameters": {
                "type": "object",
                "properties": {
                    "note": {
                        "type": "string",
                        "description": "The note to save"
                    }
                },
                "required": ["note"]
            }
        }
    }
]


def execute_tool(tool_name: str, arguments: dict) -> Any:
    """Execute a tool by name."""
    tools = {
        "web_search": web_search,
        "save_note": save_note,
    }

    if tool_name not in tools:
        return {"error": f"Unknown tool: {tool_name}"}

    return tools[tool_name](**arguments)
