"""
Tools for the Naive Research Agent (v1)

Research-focused tools for web search, content extraction, and note-taking.
This is the baseline implementation - later versions will improve on this.
"""

import json
import os
from datetime import datetime
from typing import Any

# =============================================================================
# Tool Definitions (JSON Schema for LLM)
# =============================================================================

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the web for information on any topic. Returns a list of relevant results with titles, URLs, and content snippets.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to find relevant information"
                    },
                    "num_results": {
                        "type": "integer",
                        "description": "Number of results to return (1-10). Defaults to 5.",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_page_content",
            "description": "Fetch and extract the main content from a webpage URL. Use this to get more detailed information from a specific source.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL of the webpage to extract content from"
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
            "description": "Save an important finding or piece of information discovered during research. Use this to keep track of key facts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "The topic or category of this finding"
                    },
                    "content": {
                        "type": "string",
                        "description": "The finding or information to save"
                    },
                    "source": {
                        "type": "string",
                        "description": "The source URL or reference for this finding"
                    }
                },
                "required": ["topic", "content"]
            }
        }
    }
]


# =============================================================================
# Tool Implementations
# =============================================================================

def web_search(query: str, num_results: int = 5) -> dict[str, Any]:
    """
    Search the web using Tavily API.
    Falls back to mock data if API key is not configured.
    """
    tavily_api_key = os.getenv("TAVILY_API_KEY")

    if tavily_api_key:
        try:
            from tavily import TavilyClient

            client = TavilyClient(api_key=tavily_api_key)
            response = client.search(
                query=query,
                max_results=num_results,
                search_depth="basic",
                include_answer=True
            )

            results = []
            for item in response.get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("content", "")[:500]
                })

            return {
                "success": True,
                "query": query,
                "answer": response.get("answer", ""),
                "num_results": len(results),
                "results": results
            }

        except Exception as e:
            return {
                "success": False,
                "query": query,
                "error": f"Search failed: {str(e)}"
            }
    else:
        # Mock results for demo without API key
        return _mock_search(query, num_results)


def _mock_search(query: str, num_results: int) -> dict[str, Any]:
    """Generate mock search results for demo purposes."""
    print(f"[Mock] Searching for: {query}")

    mock_results = [
        {
            "title": f"Understanding {query}: A Comprehensive Guide",
            "url": f"https://example.com/guide/{query.replace(' ', '-').lower()}",
            "content": f"This comprehensive guide covers everything you need to know about {query}. We explore the key concepts, latest developments, and practical applications in this field."
        },
        {
            "title": f"{query} - Latest News and Updates 2024",
            "url": f"https://news.example.com/{query.replace(' ', '-').lower()}",
            "content": f"Stay up to date with the latest news about {query}. Recent developments show significant progress in this area, with experts predicting continued growth and innovation."
        },
        {
            "title": f"Expert Analysis: The Future of {query}",
            "url": f"https://analysis.example.com/{query.replace(' ', '-').lower()}",
            "content": f"Industry experts weigh in on the future of {query}. Key trends include increased adoption, technological improvements, and expanding use cases across multiple sectors."
        },
        {
            "title": f"{query} Research Paper - Academic Review",
            "url": f"https://academic.example.com/{query.replace(' ', '-').lower()}",
            "content": f"Academic research on {query} reveals important findings. This peer-reviewed study examines the fundamental aspects and provides data-driven insights for practitioners."
        },
        {
            "title": f"How {query} is Changing the Industry",
            "url": f"https://industry.example.com/{query.replace(' ', '-').lower()}",
            "content": f"Discover how {query} is transforming industries worldwide. Companies are leveraging these innovations to improve efficiency, reduce costs, and drive sustainable growth."
        }
    ]

    return {
        "success": True,
        "query": query,
        "answer": f"Based on search results, {query} is a topic of significant interest with multiple perspectives and ongoing developments in the field.",
        "num_results": min(num_results, len(mock_results)),
        "results": mock_results[:num_results],
        "note": "Mock data - set TAVILY_API_KEY for real results"
    }


def get_page_content(url: str) -> dict[str, Any]:
    """
    Fetch and extract content from a webpage.
    Uses Tavily extract or falls back to mock.
    """
    tavily_api_key = os.getenv("TAVILY_API_KEY")

    if tavily_api_key:
        try:
            from tavily import TavilyClient

            client = TavilyClient(api_key=tavily_api_key)
            response = client.extract(urls=[url])

            if response.get("results"):
                result = response["results"][0]
                return {
                    "success": True,
                    "url": url,
                    "content": result.get("raw_content", "")[:3000]
                }
            else:
                return {
                    "success": False,
                    "url": url,
                    "error": "No content extracted"
                }

        except Exception as e:
            return {
                "success": False,
                "url": url,
                "error": f"Extraction failed: {str(e)}"
            }
    else:
        # Mock content for demo
        print(f"[Mock] Extracting content from: {url}")
        return {
            "success": True,
            "url": url,
            "content": f"[Mock content for {url}]\n\nThis is simulated webpage content for demonstration purposes. The page contains detailed information about the topic, including background context, current state of the art, key players in the field, and future outlook.\n\nKey points covered:\n1. Introduction and overview\n2. Historical background\n3. Current developments\n4. Future predictions\n5. Practical applications\n\nIn production with TAVILY_API_KEY set, this would contain the actual extracted content from the webpage.",
            "note": "Mock data - set TAVILY_API_KEY for real content"
        }


# In-memory storage for findings
_findings: list[dict] = []


def save_finding(topic: str, content: str, source: str = None) -> dict[str, Any]:
    """Save a research finding."""
    finding = {
        "id": len(_findings) + 1,
        "topic": topic,
        "content": content,
        "source": source or "Unknown",
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    _findings.append(finding)
    print(f"[Finding saved] {topic}: {content[:50]}...")

    return {
        "success": True,
        "message": f"Finding saved: {topic}",
        "finding_id": finding["id"],
        "total_findings": len(_findings)
    }


def get_all_findings() -> list[dict]:
    """Get all saved findings."""
    return _findings.copy()


def clear_findings():
    """Clear all findings (for testing)."""
    global _findings
    _findings = []


# =============================================================================
# Tool Dispatcher
# =============================================================================

TOOL_IMPLEMENTATIONS = {
    "web_search": web_search,
    "get_page_content": get_page_content,
    "save_finding": save_finding,
}


def execute_tool(tool_name: str, arguments: dict[str, Any]) -> str:
    """Execute a tool by name with given arguments."""
    if tool_name not in TOOL_IMPLEMENTATIONS:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})

    try:
        result = TOOL_IMPLEMENTATIONS[tool_name](**arguments)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})
