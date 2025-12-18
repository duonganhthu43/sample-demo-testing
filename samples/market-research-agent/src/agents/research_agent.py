"""
Research Agent - FLATTENED (Deterministic Execution)
Responsible for gathering information from various sources
NO internal agentic loop - only deterministic execution for speed
"""

import time
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..utils.config import get_config
from ..utils.schemas import get_response_format, RESEARCH_SYNTHESIS_SCHEMA
from ..tools import WebSearchTool, DataExtractor


@dataclass
class ResearchResult:
    """Research result data structure"""
    topic: str
    research_type: str
    summary: str
    findings: List[Dict[str, Any]] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    confidence: float = 0.0
    timestamp: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "topic": self.topic,
            "research_type": self.research_type,
            "summary": self.summary,
            "findings": self.findings,
            "sources": self.sources,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }


class ResearchAgent:
    """
    Agent specialized in gathering and synthesizing research
    FLATTENED: No internal agentic loop - deterministic execution
    """

    def __init__(self, config: Optional[Any] = None):
        self.config = config or get_config()
        self.llm_client = self.config.get_llm_client(label="research_agent")
        self.llm_params = self.config.get_llm_params()

        # Tools
        self.search_tool = WebSearchTool()
        self.data_extractor = DataExtractor()

        print(f"ResearchAgent initialized (deterministic mode - FAST)")

    def research_company(self, company_name: str, depth: str = "standard") -> ResearchResult:
        """
        Research a company comprehensively (DETERMINISTIC)

        Args:
            company_name: Name of the company to research
            depth: Research depth (quick, standard, deep)

        Returns:
            ResearchResult with company information
        """
        start_time = time.time()
        print(f"\n🔍 ResearchAgent - Company: {company_name} (depth: {depth})")

        # Determine search/extract count based on depth
        search_counts = {"quick": 2, "standard": 3, "deep": 5}
        extract_counts = {"quick": 2, "standard": 4, "deep": 6}

        num_searches = search_counts.get(depth, 3)
        num_extracts = extract_counts.get(depth, 4)

        # Execute searches
        all_results = []
        all_urls = []

        search_queries = [
            f"{company_name} company overview products business model",
            f"{company_name} headquarters employees revenue funding",
            f"{company_name} technology innovation competitive advantage",
            f"{company_name} market position customers growth",
            f"{company_name} recent news developments strategy"
        ][:num_searches]

        print(f"  → Executing {num_searches} web searches...")
        for query in search_queries:
            results = self.search_tool.search(query, num_results=3)
            all_results.extend([r.to_dict() for r in results])
            all_urls.extend([r.url for r in results if r.url])

        # Extract from top URLs
        unique_urls = list(dict.fromkeys(all_urls))[:num_extracts]
        extracted_content = []

        if unique_urls:
            print(f"  → Extracting from {len(unique_urls)} URLs...")
            for url in unique_urls:
                content = self.data_extractor.extract_from_url(url)
                if content:
                    # content is already a dict with url, title, description, text
                    extracted_content.append(content)

        # Synthesize with ONE LLM call
        print(f"  → Synthesizing findings...")
        synthesis = self._synthesize_research(
            topic=company_name,
            research_type="company",
            search_results=all_results,
            extracted_content=extracted_content
        )

        duration = time.time() - start_time
        print(f"✅ ResearchAgent complete - {duration:.2f}s ({num_searches} searches, {len(extracted_content)} extracts, 1 LLM call)\n")

        return ResearchResult(
            topic=company_name,
            research_type="company",
            summary=synthesis.get("summary", ""),
            findings=synthesis.get("findings", []),
            sources=unique_urls,
            confidence=synthesis.get("confidence", 0.7),
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            metadata={"depth": depth, "num_searches": num_searches, "num_extracts": len(extracted_content)}
        )

    def research_market(self, market_name: str, depth: str = "standard") -> ResearchResult:
        """
        Research a market or industry (DETERMINISTIC)

        Args:
            market_name: Name of the market/industry
            depth: Research depth

        Returns:
            ResearchResult with market information
        """
        start_time = time.time()
        print(f"\n🔍 ResearchAgent - Market: {market_name} (depth: {depth})")

        # Determine counts based on depth
        search_counts = {"quick": 2, "standard": 3, "deep": 5}
        extract_counts = {"quick": 2, "standard": 4, "deep": 6}

        num_searches = search_counts.get(depth, 3)
        num_extracts = extract_counts.get(depth, 4)

        # Execute searches
        all_results = []
        all_urls = []

        search_queries = [
            f"{market_name} market size growth rate forecast",
            f"{market_name} industry trends key drivers",
            f"{market_name} market leaders competitive landscape",
            f"{market_name} market segments opportunities",
            f"{market_name} industry analysis market dynamics"
        ][:num_searches]

        print(f"  → Executing {num_searches} web searches...")
        for query in search_queries:
            results = self.search_tool.search(query, num_results=3)
            all_results.extend([r.to_dict() for r in results])
            all_urls.extend([r.url for r in results if r.url])

        # Extract from top URLs
        unique_urls = list(dict.fromkeys(all_urls))[:num_extracts]
        extracted_content = []

        if unique_urls:
            print(f"  → Extracting from {len(unique_urls)} URLs...")
            for url in unique_urls:
                content = self.data_extractor.extract_from_url(url)
                if content:
                    # content is already a dict with url, title, description, text
                    extracted_content.append(content)

        # Synthesize with ONE LLM call
        print(f"  → Synthesizing findings...")
        synthesis = self._synthesize_research(
            topic=market_name,
            research_type="market",
            search_results=all_results,
            extracted_content=extracted_content
        )

        duration = time.time() - start_time
        print(f"✅ ResearchAgent complete - {duration:.2f}s ({num_searches} searches, {len(extracted_content)} extracts, 1 LLM call)\n")

        return ResearchResult(
            topic=market_name,
            research_type="market",
            summary=synthesis.get("summary", ""),
            findings=synthesis.get("findings", []),
            sources=unique_urls,
            confidence=synthesis.get("confidence", 0.7),
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            metadata={"depth": depth, "num_searches": num_searches, "num_extracts": len(extracted_content)}
        )

    def research_competitors(self, company_name: str, industry: str, depth: str = "standard") -> ResearchResult:
        """
        Research competitors in an industry (DETERMINISTIC)

        Args:
            company_name: Reference company
            industry: Industry to research
            depth: Research depth

        Returns:
            ResearchResult with competitor information
        """
        start_time = time.time()
        print(f"\n🔍 ResearchAgent - Competitors: {company_name} in {industry} (depth: {depth})")

        # Determine counts based on depth
        search_counts = {"quick": 2, "standard": 3, "deep": 4}
        extract_counts = {"quick": 2, "standard": 3, "deep": 5}

        num_searches = search_counts.get(depth, 3)
        num_extracts = extract_counts.get(depth, 3)

        # Execute searches
        all_results = []
        all_urls = []

        search_queries = [
            f"{company_name} competitors {industry}",
            f"{industry} market leaders competitive landscape",
            f"{company_name} vs competitors comparison",
            f"{industry} top companies market share"
        ][:num_searches]

        print(f"  → Executing {num_searches} web searches...")
        for query in search_queries:
            results = self.search_tool.search(query, num_results=3)
            all_results.extend([r.to_dict() for r in results])
            all_urls.extend([r.url for r in results if r.url])

        # Extract from top URLs
        unique_urls = list(dict.fromkeys(all_urls))[:num_extracts]
        extracted_content = []

        if unique_urls:
            print(f"  → Extracting from {len(unique_urls)} URLs...")
            for url in unique_urls:
                content = self.data_extractor.extract_from_url(url)
                if content:
                    # content is already a dict with url, title, description, text
                    extracted_content.append(content)

        # Synthesize with ONE LLM call
        print(f"  → Synthesizing findings...")
        synthesis = self._synthesize_research(
            topic=f"Competitors of {company_name}",
            research_type="competitors",
            search_results=all_results,
            extracted_content=extracted_content
        )

        duration = time.time() - start_time
        print(f"✅ ResearchAgent complete - {duration:.2f}s ({num_searches} searches, {len(extracted_content)} extracts, 1 LLM call)\n")

        return ResearchResult(
            topic=f"Competitors of {company_name}",
            research_type="competitors",
            summary=synthesis.get("summary", ""),
            findings=synthesis.get("findings", []),
            sources=unique_urls,
            confidence=synthesis.get("confidence", 0.7),
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            metadata={"company": company_name, "industry": industry, "depth": depth,
                     "num_searches": num_searches, "num_extracts": len(extracted_content)}
        )

    def _synthesize_research(
        self,
        topic: str,
        research_type: str,
        search_results: List[Dict[str, Any]],
        extracted_content: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Synthesize research findings with ONE LLM call (no tool calling loop)

        Args:
            topic: Research topic
            research_type: Type of research
            search_results: Search results
            extracted_content: Extracted content from URLs

        Returns:
            Synthesized findings as dict
        """
        # Build context from gathered data
        context = {
            "topic": topic,
            "research_type": research_type,
            "search_results": search_results[:10],  # Limit to top 10
            "extracted_content": extracted_content[:5]  # Limit to top 5
        }

        prompt = f"""Synthesize the following research on "{topic}" (type: {research_type}).

Search Results:
{json.dumps(search_results[:10], indent=2)}

Extracted Content:
{json.dumps(extracted_content[:5], indent=2)}

Provide a comprehensive synthesis in JSON format:
{{
  "summary": "A comprehensive 3-5 sentence summary of key findings",
  "findings": [
    {{"category": "Overview", "finding": "specific finding", "evidence": "supporting evidence"}},
    {{"category": "Key Facts", "finding": "specific finding", "evidence": "supporting evidence"}},
    ...
  ],
  "confidence": 0.8  // 0.0-1.0 based on data quality
}}

Focus on actionable insights and concrete facts. Be specific."""

        try:
            response = self.llm_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a research synthesis expert. Analyze data and provide structured insights."},
                    {"role": "user", "content": prompt}
                ],
                response_format=get_response_format("research_synthesis", RESEARCH_SYNTHESIS_SCHEMA),
                **self.llm_params
            )

            result = json.loads(response.choices[0].message.content)
            return result
        except Exception as e:
            print(f"⚠️ Synthesis failed: {e}")
            return {
                "summary": f"Research completed on {topic}. Data gathered but synthesis encountered an error.",
                "findings": [],
                "confidence": 0.5
            }
