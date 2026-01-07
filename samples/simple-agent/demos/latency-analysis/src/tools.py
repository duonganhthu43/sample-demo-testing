"""
Latency Analysis Demo - Tools with Varying Latencies

Some tools are fast, one tool is SLOW (simulated bottleneck).
"""

import os
import time
import requests
from typing import Any


def web_search(query: str) -> dict:
    """Fast search - normal latency."""
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

    # Small delay to simulate network
    time.sleep(0.3)

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


def slow_analysis(data: str) -> dict:
    """
    SLOW operation - simulates a bottleneck.

    This represents heavy processing like:
    - Large document parsing
    - Complex computation
    - Slow external API
    """
    print("[Tools] Starting slow analysis... (this will take ~3s)")

    # Simulate heavy processing - THIS IS THE BOTTLENECK
    time.sleep(3.0)

    print("[Tools] Slow analysis complete")

    return {
        "status": "complete",
        "analysis": f"Analyzed: {data[:100]}...",
        "insights": [
            "Key finding 1: Important trend identified",
            "Key finding 2: Potential opportunity",
            "Key finding 3: Risk factor detected"
        ],
        "processing_time_ms": 3000
    }


def quick_summary(text: str) -> dict:
    """Fast summary - normal latency."""
    time.sleep(0.2)  # Small delay
    return {
        "summary": f"Summary of: {text[:50]}...",
        "word_count": len(text.split())
    }


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for information (fast)",
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
            "name": "slow_analysis",
            "description": "Perform deep analysis on data (slow but thorough)",
            "parameters": {
                "type": "object",
                "properties": {
                    "data": {
                        "type": "string",
                        "description": "The data to analyze"
                    }
                },
                "required": ["data"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "quick_summary",
            "description": "Create a quick summary of text (fast)",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text to summarize"
                    }
                },
                "required": ["text"]
            }
        }
    }
]


def execute_tool(tool_name: str, arguments: dict) -> Any:
    """Execute a tool by name."""
    tools = {
        "web_search": web_search,
        "slow_analysis": slow_analysis,
        "quick_summary": quick_summary,
    }

    if tool_name not in tools:
        return {"error": f"Unknown tool: {tool_name}"}

    return tools[tool_name](**arguments)
