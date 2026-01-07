"""
Hidden Issues Demo - Tools that return "successful" responses with hidden problems

These tools demonstrate scenarios where:
1. HTTP status is 200 / no error field
2. But content contains semantic errors humans would miss
3. Issues are buried in long responses or spread across calls
"""

import os
import time
import requests
from typing import Any

# Track call counts to simulate degrading responses
_search_call_count = 0
_api_call_count = 0


def reset_call_counts():
    """Reset call counters for fresh demo run."""
    global _search_call_count, _api_call_count
    _search_call_count = 0
    _api_call_count = 0


def web_search(query: str) -> dict:
    """
    Search that returns "success" but with hidden issues.

    Each subsequent call has a different subtle problem:
    - Call 1: Works but has warning buried in content
    - Call 2: Empty results with polite message
    - Call 3: Rate limited, returns stale cache
    - Call 4+: Degraded responses
    """
    global _search_call_count
    _search_call_count += 1
    call_num = _search_call_count

    # Try real Tavily first
    tavily_key = os.getenv("TAVILY_API_KEY")
    if tavily_key and tavily_key.startswith("tvly-") and call_num == 1:
        try:
            response = requests.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": tavily_key,
                    "query": query,
                    "search_depth": "basic",
                    "max_results": 2
                },
                timeout=30
            )
            response.raise_for_status()
            real_results = response.json()
            # Add hidden warning to real results
            real_results["_metadata"] = {
                "warning": "Some results may be from unverified sources. Primary database connection failed, using secondary index.",
                "freshness": "Results cached from previous query, may not reflect latest data"
            }
            return real_results
        except:
            pass

    # Simulate different hidden issues based on call number
    if call_num == 1:
        # First call: Looks good but has buried warning
        return {
            "status": "success",
            "query": query,
            "results": [
                {
                    "title": f"Understanding {query}",
                    "url": f"https://example.com/{query.replace(' ', '-')}-guide",
                    "content": f"""Comprehensive guide about {query}. This article covers the fundamentals
                    and advanced concepts. Key topics include definition, history, and applications.

                    NOTE: This content was retrieved from cached index dated 2019-03-15.
                    WARNING: Failed to connect to primary data source (connection timeout after 30s).
                    Falling back to secondary cache which may contain outdated information.

                    The field of {query} has evolved significantly. Recent developments include
                    improved methodologies and new frameworks. Experts recommend staying updated
                    with the latest research publications for current information.""",
                    "score": 0.92
                }
            ],
            "total_results": 1,
            "_metadata": {"source": "cache", "cache_date": "2019-03-15"}
        }

    elif call_num == 2:
        # Second call: Empty results, polite message (silent failure)
        return {
            "status": "success",  # No error field!
            "query": query,
            "results": [],  # Empty!
            "total_results": 0,
            "message": "Search completed successfully but could not find any relevant results matching your query. The search index may not contain information on this specific topic.",
            "_metadata": {"searched_indices": 3, "matched": 0}
        }

    elif call_num == 3:
        # Third call: Rate limited, stale cache
        time.sleep(0.5)  # Simulate slowdown
        return {
            "status": "success",
            "query": query,
            "results": [
                {
                    "title": f"Cached: {query} Overview",
                    "url": f"https://archive.example.com/{query.replace(' ', '-')}",
                    "content": f"[CACHED RESULT - Original source unavailable] Basic overview of {query}. Rate limit exceeded on primary API (429 Too Many Requests). Serving from local cache. This information was last verified on 2021-06-20 and may not reflect current state.",
                    "score": 0.65,
                    "cached": True
                }
            ],
            "total_results": 1,
            "_rate_limit": {
                "status": "exceeded",
                "retry_after": 3600,
                "message": "API rate limit reached. Using cached fallback."
            }
        }

    elif call_num == 4:
        # Fourth call: Partial failure
        return {
            "status": "partial_success",
            "query": query,
            "results": [
                {
                    "title": f"Limited: {query}",
                    "url": f"https://example.com/{query.replace(' ', '-')}-limited",
                    "content": f"Partial information about {query}. [DATA TRUNCATED: Maximum response size exceeded. Only 10% of content retrieved. Full document unavailable due to service degradation.]",
                    "score": 0.45,
                    "truncated": True
                }
            ],
            "total_results": 1,
            "warnings": ["Response truncated", "Service experiencing high load"]
        }

    else:
        # Fifth+ call: Looks okay but content indicates nothing found
        return {
            "status": "success",
            "query": query,
            "results": [
                {
                    "title": f"Search: {query}",
                    "url": f"https://example.com/search?q={query.replace(' ', '+')}",
                    "content": f"No matching documents found for '{query}'. The query did not match any indexed content. Suggestions: Try different keywords, check spelling, or broaden your search terms. Query expansion attempted but yielded no additional results.",
                    "score": 0.20
                }
            ],
            "total_results": 1
        }


def fetch_document(url: str) -> dict:
    """
    Fetch document that returns success but with hidden issues.
    """
    global _api_call_count
    _api_call_count += 1

    # Simulate long response with buried warning
    padding_before = "This document contains comprehensive information. " * 50
    padding_after = "For more information, consult additional sources. " * 50

    hidden_warning = """

    ============================================================
    INTERNAL NOTE: Document retrieval encountered issues.
    - Primary CDN returned 503 Service Unavailable
    - Fallback to origin server succeeded but with degraded performance
    - Document checksum mismatch detected (expected: abc123, got: xyz789)
    - Content may be corrupted or from incorrect version
    - Last successful full retrieval: 2020-11-15
    ============================================================

    """

    return {
        "status": "success",
        "url": url,
        "content": padding_before + hidden_warning + padding_after,
        "content_type": "text/html",
        "retrieved_at": "2024-01-15T10:30:00Z",
        "content_length": len(padding_before) + len(hidden_warning) + len(padding_after)
    }


def analyze_content(text: str) -> dict:
    """
    Analysis that appears successful but notes it couldn't process properly.
    """
    return {
        "status": "completed",
        "analysis": {
            "summary": f"Analysis of provided content ({len(text)} characters).",
            "key_points": [
                "Point 1: General information identified",
                "Point 2: Some relevant concepts found",
                "Point 3: Unable to extract specific details due to content quality issues"
            ],
            "confidence": 0.45,  # Low confidence but no error
            "warnings": [
                "Input text contained malformed sections that could not be parsed",
                "Confidence score below recommended threshold (0.70)",
                "Some assertions could not be verified against knowledge base"
            ],
            "quality_score": "low"  # Hidden quality indicator
        }
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
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_document",
            "description": "Fetch and extract content from a URL",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to fetch"
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "analyze_content",
            "description": "Analyze text content and extract key information",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The text to analyze"
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
        "fetch_document": fetch_document,
        "analyze_content": analyze_content,
    }

    if tool_name not in tools:
        return {"error": f"Unknown tool: {tool_name}"}

    return tools[tool_name](**arguments)
