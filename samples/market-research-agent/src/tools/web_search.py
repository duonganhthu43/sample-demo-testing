"""
Web Search Tool
Provides web search capabilities using various APIs
"""

import os
from typing import List, Dict, Any, Optional
import time
import json

from ..utils.config import get_config


class SearchResult:
    """Search result data structure"""

    def __init__(self, title: str, url: str, snippet: str, source: str = ""):
        self.title = title
        self.url = url
        self.snippet = snippet
        self.source = source

    def to_dict(self) -> Dict[str, str]:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source": self.source
        }

    def __repr__(self) -> str:
        return f"SearchResult(title='{self.title[:50]}...', url='{self.url}')"


class WebSearchTool:
    """
    Web search tool that supports multiple search providers
    """

    # In-memory cache for search results (shared across instances)
    _search_cache: Dict[tuple, List["SearchResult"]] = {}

    def __init__(self, provider: Optional[str] = None):
        self.config = get_config()
        self.provider = provider or self.config.search.provider
        self.mock_mode = self.config.app.mock_external_apis

        # Auto-enable mock mode if API keys are missing
        if self.provider == "serpapi" and not self.config.search.serpapi_api_key:
            self.mock_mode = True
            print("SerpAPI key not found - using mock mode")
        elif self.provider == "tavily" and not self.config.search.tavily_api_key:
            self.mock_mode = True
            print("Tavily key not found - using mock mode")

        print(f"Initialized WebSearchTool with provider: {self.provider}, mock_mode: {self.mock_mode}")

    def search(self, query: str, num_results: int = 10, deep: bool = False) -> List[SearchResult]:
        """
        Perform web search

        Args:
            query: Search query string
            num_results: Number of results to return
            deep: Use advanced/deep search (slower but more thorough)

        Returns:
            List of SearchResult objects
        """
        # Check cache first
        cache_key = (query, num_results, deep)
        if cache_key in WebSearchTool._search_cache:
            print(f"Cache hit for: '{query}' (limit: {num_results}, deep: {deep})")
            return WebSearchTool._search_cache[cache_key]

        print(f"Searching: '{query}' (limit: {num_results}, deep: {deep})")

        if self.mock_mode:
            results = self._mock_search(query, num_results)
        elif self.provider == "serpapi":
            results = self._search_serpapi(query, num_results)
        elif self.provider == "tavily":
            results = self._search_tavily(query, num_results, deep)
        else:
            raise ValueError(f"Unsupported search provider: {self.provider}")

        # Store in cache
        WebSearchTool._search_cache[cache_key] = results
        return results

    def _search_serpapi(self, query: str, num_results: int) -> List[SearchResult]:
        """Search using SerpAPI (Google Search)"""
        try:
            from serpapi import GoogleSearch

            params = {
                "q": query,
                "api_key": self.config.search.serpapi_api_key,
                "num": num_results,
            }

            search = GoogleSearch(params)
            results = search.get_dict()

            search_results = []

            # Process organic results
            if "organic_results" in results:
                for result in results["organic_results"][:num_results]:
                    search_results.append(SearchResult(
                        title=result.get("title", ""),
                        url=result.get("link", ""),
                        snippet=result.get("snippet", ""),
                        source="google"
                    ))

            print(f"Found {len(search_results)} results via SerpAPI")
            return search_results

        except Exception as e:
            print(f"SerpAPI search failed: {str(e)}")
            return self._mock_search(query, num_results)

    def _search_tavily(self, query: str, num_results: int, deep: bool = False) -> List[SearchResult]:
        """Search using Tavily API"""
        try:
            from tavily import TavilyClient

            client = TavilyClient(api_key=self.config.search.tavily_api_key)
            search_depth = "advanced" if deep else "basic"

            response = client.search(
                query=query,
                max_results=num_results,
                search_depth=search_depth
            )

            search_results = []

            for result in response.get("results", [])[:num_results]:
                search_results.append(SearchResult(
                    title=result.get("title", ""),
                    url=result.get("url", ""),
                    snippet=result.get("content", ""),
                    source="tavily"
                ))

            print(f"Found {len(search_results)} results via Tavily")
            return search_results

        except Exception as e:
            print(f"Tavily search failed: {str(e)}")
            return self._mock_search(query, num_results)

    def _mock_search(self, query: str, num_results: int) -> List[SearchResult]:
        """
        Mock search for testing without API keys
        Returns realistic-looking mock data
        """
        print("Using mock search results")

        # Generate mock results based on query
        mock_results = []

        # Check what the query is about
        query_lower = query.lower()

        if "ai" in query_lower or "artificial intelligence" in query_lower:
            mock_data = [
                {
                    "title": "The State of AI in 2024: Latest Trends and Developments",
                    "url": "https://www.techcrunch.com/ai-trends-2024",
                    "snippet": "Comprehensive analysis of AI industry trends, including generative AI adoption, enterprise use cases, and market growth projections for 2024 and beyond."
                },
                {
                    "title": "Top AI Companies Leading the Industry",
                    "url": "https://www.forbes.com/top-ai-companies",
                    "snippet": "OpenAI, Anthropic, Google DeepMind, and other leading companies shaping the AI landscape through innovative products and research."
                },
                {
                    "title": "Market Research: AI Industry Size and Growth",
                    "url": "https://www.gartner.com/ai-market-research",
                    "snippet": "The global AI market is projected to reach $1.8 trillion by 2030, driven by enterprise adoption, automation, and productivity improvements."
                }
            ]
        elif "market" in query_lower or "industry" in query_lower:
            mock_data = [
                {
                    "title": "Industry Analysis and Market Insights 2024",
                    "url": "https://www.mckinsey.com/industry-analysis-2024",
                    "snippet": "Detailed market analysis covering market size, growth trends, competitive landscape, and future projections across major industries."
                },
                {
                    "title": "Market Research Report: Key Findings",
                    "url": "https://www.statista.com/market-research",
                    "snippet": "Comprehensive market data including revenue forecasts, market share analysis, and consumer behavior trends."
                }
            ]
        else:
            # Generic results
            mock_data = [
                {
                    "title": f"Everything you need to know about {query}",
                    "url": f"https://www.example.com/{query.replace(' ', '-')}",
                    "snippet": f"Comprehensive guide and analysis of {query}, including latest developments, key players, and market trends."
                },
                {
                    "title": f"{query}: Market Analysis and Insights",
                    "url": f"https://www.research.com/{query.replace(' ', '-')}-analysis",
                    "snippet": f"In-depth market research covering {query} industry size, growth projections, and competitive landscape."
                },
                {
                    "title": f"Latest News and Updates on {query}",
                    "url": f"https://www.news.com/{query.replace(' ', '-')}-updates",
                    "snippet": f"Recent developments and news articles about {query}, including expert opinions and analysis."
                }
            ]

        # Add more generic results to reach num_results
        while len(mock_data) < num_results:
            idx = len(mock_data) + 1
            mock_data.append({
                "title": f"Research Report #{idx} about {query}",
                "url": f"https://www.research{idx}.com/{query.replace(' ', '-')}",
                "snippet": f"Additional information and insights about {query} from industry experts and market analysts."
            })

        for data in mock_data[:num_results]:
            mock_results.append(SearchResult(
                title=data["title"],
                url=data["url"],
                snippet=data["snippet"],
                source="mock"
            ))

        print(f"Generated {len(mock_results)} mock results")
        return mock_results

    def search_news(self, query: str, num_results: int = 5) -> List[SearchResult]:
        """
        Search for recent news articles

        Args:
            query: Search query
            num_results: Number of results

        Returns:
            List of news SearchResult objects
        """
        # Add "news" to query for better results
        news_query = f"{query} news latest"
        return self.search(news_query, num_results)

    def search_company(self, company_name: str) -> List[SearchResult]:
        """
        Search for company information

        Args:
            company_name: Name of the company

        Returns:
            List of SearchResult objects about the company
        """
        queries = [
            f"{company_name} company overview",
            f"{company_name} products services",
            f"{company_name} revenue business model",
            f"{company_name} competitors market share",
        ]

        all_results = []
        for query in queries:
            results = self.search(query, num_results=3)
            all_results.extend(results)

        return all_results

    def format_results(self, results: List[SearchResult], max_snippet_length: int = 200) -> str:
        """
        Format search results as a readable string

        Args:
            results: List of SearchResult objects
            max_snippet_length: Maximum length for snippets

        Returns:
            Formatted string of results
        """
        if not results:
            return "No search results found."

        formatted = []
        for i, result in enumerate(results, 1):
            snippet = result.snippet[:max_snippet_length]
            if len(result.snippet) > max_snippet_length:
                snippet += "..."

            formatted.append(f"{i}. {result.title}\n   URL: {result.url}\n   {snippet}\n")

        return "\n".join(formatted)


# Convenience function
def search_web(query: str, num_results: int = 10, deep: bool = False) -> List[SearchResult]:
    """
    Convenience function to perform web search

    Args:
        query: Search query
        num_results: Number of results
        deep: Use advanced/deep search (slower but more thorough)

    Returns:
        List of SearchResult objects
    """
    tool = WebSearchTool()
    return tool.search(query, num_results, deep)
