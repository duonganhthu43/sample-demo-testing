"""
Simple Agent v5 - Tools with Semantic Errors

THIS VERSION HAS INTENTIONAL BUGS FOR TESTING DEBUG TRACING.

Bugs in this file:
1. Tool name mismatch: TOOL_DEFINITIONS uses "search_web" but execute_tool expects "web_search"
2. Missing required parameter: "num_results" is used in code but not in tool schema
3. Type confusion: get_page_content returns dict but some places expect string
"""

import os
import json
import requests
from typing import Any

# Global storage for findings
_findings = []


def get_all_findings() -> list[dict]:
    """Get all saved findings."""
    return _findings.copy()


def clear_findings():
    """Clear all findings."""
    global _findings
    _findings = []


# =============================================================================
# BUG #1: Tool name mismatch
# The function is named "web_search" but TOOL_DEFINITIONS calls it "search_web"
# =============================================================================
def web_search(query: str, num_results: int = 5) -> dict:
    """
    Search the web using Tavily API or return mock results.

    Args:
        query: Search query string
        num_results: Number of results to return (BUG: not in tool schema!)

    Returns:
        Dict with search results
    """
    tavily_key = os.getenv("TAVILY_API_KEY")

    if tavily_key and tavily_key.startswith("tvly-"):
        try:
            response = requests.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": tavily_key,
                    "query": query,
                    "search_depth": "basic",
                    "max_results": num_results
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
                "content": f"Comprehensive guide about {query}. This covers the fundamentals and advanced concepts.",
                "score": 0.95
            },
            {
                "title": f"{query} - Wikipedia",
                "url": f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}",
                "content": f"Wikipedia article about {query} with detailed information and references.",
                "score": 0.90
            },
            {
                "title": f"Latest {query} Trends 2024",
                "url": f"https://example.com/{query.replace(' ', '-')}-trends",
                "content": f"Analysis of recent developments and trends in {query}.",
                "score": 0.85
            }
        ]
    }


def get_page_content(url: str) -> dict:
    """
    Extract content from a URL.

    BUG #3: Returns dict but some code paths treat it as string
    """
    # In production, would use requests + BeautifulSoup
    # For demo, return mock content
    return {
        "url": url,
        "content": f"Mock content extracted from {url}. This would contain the actual page text in a real implementation.",
        "title": f"Page: {url.split('/')[-1]}",
        "extracted_at": "2024-01-15T10:30:00Z"
    }


def save_finding(finding: str, source: str = "unknown") -> dict:
    """Save a research finding."""
    global _findings
    entry = {
        "finding": finding,
        "source": source,
        "index": len(_findings)
    }
    _findings.append(entry)
    return {"status": "saved", "index": entry["index"]}


# =============================================================================
# BUG #1: Tool name is "search_web" here but function is "web_search"
# BUG #2: Missing "num_results" parameter that the function actually uses
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
                    # BUG: Missing "num_results" parameter!
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_page_content",
            "description": "Extract content from a webpage URL",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to extract content from"
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_finding",
            "description": "Save an important finding from the research",
            "parameters": {
                "type": "object",
                "properties": {
                    "finding": {
                        "type": "string",
                        "description": "The finding to save"
                    },
                    "source": {
                        "type": "string",
                        "description": "Source of the finding"
                    }
                },
                "required": ["finding"]
            }
        }
    }
]


def execute_tool(tool_name: str, arguments: dict) -> Any:
    """
    Execute a tool by name with given arguments.

    BUG: This expects "web_search" but TOOL_DEFINITIONS defines "search_web"
    """
    tools = {
        "web_search": web_search,  # BUG: LLM will call "search_web" but this expects "web_search"
        "get_page_content": get_page_content,
        "save_finding": save_finding
    }

    if tool_name not in tools:
        # This error will occur when LLM calls "search_web" (from schema)
        # but we only have "web_search" registered
        return {"error": f"Unknown tool: {tool_name}"}

    return tools[tool_name](**arguments)
