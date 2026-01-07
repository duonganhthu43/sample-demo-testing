"""
Simple Agent v4 - Parallel Execution

This version adds parallel execution to the sub-agent architecture:
- Multiple searches run concurrently
- Parallel content extraction from URLs
- Concurrent analysis of different sources

Key improvement over v3:
- Uses ThreadPoolExecutor for parallel tool execution
- Significantly faster for multi-query research
- Same quality, better performance

Architecture:
- Same 4 sub-agents as v3 (Planner, Searcher, Analyzer, Synthesizer)
- Searcher now executes searches in parallel
- Analyzer processes results concurrently
"""

import json
import os
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Any, Optional

from openai import OpenAI

from .tools import TOOL_DEFINITIONS, execute_tool, get_all_findings, clear_findings, web_search, get_page_content


@dataclass
class ResearchResult:
    """Result from a research task"""
    question: str
    answer: str
    findings: list[dict] = field(default_factory=list)
    sources: list[str] = field(default_factory=list)
    iterations: int = 0
    tool_calls: list[dict] = field(default_factory=list)
    total_duration: float = 0.0
    thread_id: Optional[str] = None
    run_id: Optional[str] = None
    research_plan: Optional[str] = None
    sub_agent_calls: dict = field(default_factory=dict)
    # v4 additions
    parallel_searches: int = 0
    sequential_time_estimate: float = 0.0


# =============================================================================
# Sub-Agent Prompts (same as v3)
# =============================================================================

PLANNER_PROMPT = """You are a Research Planner. Your ONLY job is to analyze questions and create research plans.

Given a research question, you must:
1. Identify the key concepts that need to be understood
2. Break down complex questions into 2-4 simpler sub-questions
3. Prioritize which aspects to research first
4. Suggest specific search queries for each sub-question

OUTPUT FORMAT (respond in this exact JSON format):
{
    "main_topic": "The core topic being researched",
    "sub_questions": [
        "First sub-question to answer",
        "Second sub-question to answer"
    ],
    "search_queries": [
        "optimized search query 1",
        "optimized search query 2",
        "optimized search query 3"
    ],
    "priority_order": "Explanation of research priority"
}

IMPORTANT:
- Provide 3-5 diverse search queries to enable parallel searching
- Search queries should be 3-5 keywords, NOT full sentences
- Cover different aspects of the topic for comprehensive research"""

ANALYZER_PROMPT = """You are a Research Analyzer. Your job is to analyze search results and extract key insights.

You will receive search results from multiple parallel queries. For the content:
1. Identify the main claims and facts
2. Extract specific data points, statistics, or quotes
3. Note the most valuable sources
4. Summarize key findings

Provide a structured analysis that can be used for synthesis."""

SYNTHESIZER_PROMPT = """You are a Research Synthesizer. Your ONLY job is to combine findings into a coherent, well-structured answer.

You will receive analyzed findings from the research process. Your task:
1. Organize information logically
2. Address all aspects of the original question
3. Present a balanced view with multiple perspectives
4. Cite sources for key claims
5. Acknowledge limitations or gaps

OUTPUT REQUIREMENTS:
- Start with a clear, direct answer to the question
- Support with evidence from the research
- Use clear structure with sections if needed
- End with any caveats or areas needing more research
- Include source citations"""


class ResearchAgentV4:
    """
    Research Agent v4 with parallel execution.

    Key improvements over v3:
    1. PARALLEL SEARCHES: Multiple queries executed concurrently
    2. PARALLEL EXTRACTION: Content fetched from multiple URLs at once
    3. FASTER EXECUTION: Significant time savings for complex research

    Architecture:
    - Same sub-agents as v3
    - ThreadPoolExecutor for parallel tool execution
    - Aggregation of parallel results before synthesis
    """

    def __init__(
        self,
        model: str = None,
        max_iterations: int = 10,
        verbose: bool = True,
        thread_id: Optional[str] = None,
        run_id: Optional[str] = None,
        max_workers: int = 4  # Number of parallel workers
    ):
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.max_workers = max_workers

        # Generate observability IDs
        self.thread_id = thread_id or str(uuid.uuid4())
        self.run_id = run_id or str(uuid.uuid4())

        # Build headers for observability
        default_headers = {
            "x-thread-id": self.thread_id,
            "x-run-id": self.run_id,
            "x-label": "research-agent-v4"
        }

        # Initialize OpenAI client
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL"),
            default_headers=default_headers
        )

        self.sub_agent_calls = {
            "planner": 0,
            "searcher": 0,
            "analyzer": 0,
            "synthesizer": 0
        }

    def _log(self, message: str):
        if self.verbose:
            print(f"[Research Agent v4] {message}")

    def _call_llm(self, system_prompt: str, user_message: str) -> str:
        """Simple LLM call without tools."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ]
        )
        return response.choices[0].message.content or ""

    def _parallel_search(self, queries: list[str]) -> tuple[list[dict], float]:
        """
        Execute multiple searches in PARALLEL.

        Args:
            queries: List of search queries

        Returns:
            Tuple of (all_results, sequential_time_estimate)
        """
        self._log(f"Executing {len(queries)} searches in PARALLEL...")

        all_results = []
        sequential_estimate = 0.0

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all searches
            future_to_query = {
                executor.submit(web_search, query, 5): query
                for query in queries
            }

            # Collect results as they complete
            for future in as_completed(future_to_query):
                query = future_to_query[future]
                try:
                    start = time.time()
                    result = future.result()
                    elapsed = time.time() - start
                    sequential_estimate += elapsed

                    self._log(f"  Search completed: '{query[:30]}...'")

                    all_results.append({
                        "query": query,
                        "result": result
                    })
                except Exception as e:
                    self._log(f"  Search failed: '{query[:30]}...' - {e}")
                    all_results.append({
                        "query": query,
                        "result": {"error": str(e)}
                    })

        return all_results, sequential_estimate

    def _parallel_extract(self, urls: list[str]) -> list[dict]:
        """
        Extract content from multiple URLs in PARALLEL.

        Args:
            urls: List of URLs to extract content from

        Returns:
            List of extraction results
        """
        if not urls:
            return []

        self._log(f"Extracting content from {len(urls)} URLs in PARALLEL...")

        all_content = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {
                executor.submit(get_page_content, url): url
                for url in urls
            }

            for future in as_completed(future_to_url):
                url = future_to_url[future]
                try:
                    result = future.result()
                    self._log(f"  Extracted: {url[:50]}...")
                    all_content.append({
                        "url": url,
                        "content": result
                    })
                except Exception as e:
                    self._log(f"  Extraction failed: {url[:50]}... - {e}")

        return all_content

    def research(self, question: str) -> ResearchResult:
        """
        Research a question using parallel execution.

        Workflow:
        1. PLANNER: Create research plan with multiple queries
        2. PARALLEL SEARCH: Execute all queries concurrently
        3. PARALLEL EXTRACT: Fetch content from top URLs concurrently
        4. ANALYZER: Process all results
        5. SYNTHESIZER: Create final answer

        Args:
            question: The research question

        Returns:
            ResearchResult with answer and performance metrics
        """
        start_time = time.time()
        all_tool_calls = []
        sources = set()
        sequential_estimate = 0.0

        clear_findings()

        self._log(f"Starting research: {question[:80]}...")
        self._log(f"Thread ID: {self.thread_id}")
        self._log(f"Run ID: {self.run_id}")
        self._log(f"Max parallel workers: {self.max_workers}")

        # =================================================================
        # Step 1: PLANNER - Create research plan
        # =================================================================
        self._log("=" * 50)
        self._log("PHASE 1: PLANNING")
        self._log("=" * 50)

        self.sub_agent_calls["planner"] += 1
        plan_response = self._call_llm(
            PLANNER_PROMPT,
            f"Create a research plan for this question:\n\n{question}"
        )

        research_plan = plan_response

        # Parse search queries from plan
        search_queries = []
        try:
            import re
            json_match = re.search(r'\{[\s\S]*\}', plan_response)
            if json_match:
                plan_data = json.loads(json_match.group())
                search_queries = plan_data.get("search_queries", [])
                self._log(f"Extracted {len(search_queries)} search queries")
        except:
            search_queries = [question]
            self._log("Could not parse plan, using original question")

        # Ensure we have at least 3 queries for parallel demo
        if len(search_queries) < 3:
            # Add some derived queries
            search_queries.extend([
                f"{question} overview",
                f"{question} examples"
            ])
            search_queries = search_queries[:5]  # Cap at 5

        # =================================================================
        # Step 2: PARALLEL SEARCH
        # =================================================================
        self._log("=" * 50)
        self._log("PHASE 2: PARALLEL SEARCHING")
        self._log("=" * 50)

        self.sub_agent_calls["searcher"] += 1
        search_results, search_time_estimate = self._parallel_search(search_queries)

        sequential_estimate += search_time_estimate

        # Record tool calls
        for sr in search_results:
            all_tool_calls.append({
                "agent": "Searcher",
                "tool": "web_search",
                "arguments": {"query": sr["query"]},
                "result": sr["result"],
                "parallel": True
            })

            # Collect sources
            if sr["result"].get("results"):
                for r in sr["result"]["results"]:
                    if r.get("url"):
                        sources.add(r["url"])

        # =================================================================
        # Step 3: PARALLEL CONTENT EXTRACTION
        # =================================================================
        self._log("=" * 50)
        self._log("PHASE 3: PARALLEL CONTENT EXTRACTION")
        self._log("=" * 50)

        # Get top URLs from search results (limit to avoid too many)
        top_urls = []
        for sr in search_results:
            if sr["result"].get("results"):
                for r in sr["result"]["results"][:2]:  # Top 2 per query
                    if r.get("url") and r["url"] not in top_urls:
                        top_urls.append(r["url"])
                        if len(top_urls) >= 6:  # Max 6 extractions
                            break
            if len(top_urls) >= 6:
                break

        extracted_content = self._parallel_extract(top_urls)

        for ec in extracted_content:
            all_tool_calls.append({
                "agent": "Searcher",
                "tool": "get_page_content",
                "arguments": {"url": ec["url"]},
                "result": ec["content"],
                "parallel": True
            })

        # =================================================================
        # Step 4: ANALYZER
        # =================================================================
        self._log("=" * 50)
        self._log("PHASE 4: ANALYZING")
        self._log("=" * 50)

        self.sub_agent_calls["analyzer"] += 1

        # Compile all search results
        search_summary = "SEARCH RESULTS:\n\n"
        for sr in search_results:
            search_summary += f"Query: {sr['query']}\n"
            if sr["result"].get("results"):
                for r in sr["result"]["results"][:3]:
                    search_summary += f"  - {r.get('title', 'N/A')}: {r.get('content', '')[:200]}...\n"
            search_summary += "\n"

        # Add extracted content
        if extracted_content:
            search_summary += "\nEXTRACTED CONTENT:\n\n"
            for ec in extracted_content[:3]:  # Limit to avoid token overflow
                content = ec["content"].get("content", "")[:500]
                search_summary += f"URL: {ec['url']}\n{content}\n\n"

        analyze_prompt = f"""Original Question: {question}

Research Plan:
{plan_response}

{search_summary}

Analyze these findings and provide a structured summary of key insights."""

        analysis_response = self._call_llm(ANALYZER_PROMPT, analyze_prompt)

        # =================================================================
        # Step 5: SYNTHESIZER
        # =================================================================
        self._log("=" * 50)
        self._log("PHASE 5: SYNTHESIZING")
        self._log("=" * 50)

        self.sub_agent_calls["synthesizer"] += 1

        synthesis_prompt = f"""Original Question: {question}

Research Plan:
{plan_response}

Analysis:
{analysis_response}

Sources Used:
{json.dumps(list(sources)[:10], indent=2)}

Create a comprehensive, well-structured answer to the original question."""

        final_answer = self._call_llm(SYNTHESIZER_PROMPT, synthesis_prompt)

        total_duration = time.time() - start_time

        self._log("=" * 50)
        self._log("RESEARCH COMPLETE")
        self._log("=" * 50)
        self._log(f"Actual time: {total_duration:.2f}s")
        self._log(f"Estimated sequential time: {sequential_estimate:.2f}s")
        self._log(f"Speedup: {sequential_estimate/total_duration:.1f}x (estimated)")

        return ResearchResult(
            question=question,
            answer=final_answer,
            findings=get_all_findings(),
            sources=list(sources),
            iterations=sum(self.sub_agent_calls.values()),
            tool_calls=all_tool_calls,
            total_duration=total_duration,
            thread_id=self.thread_id,
            run_id=self.run_id,
            research_plan=research_plan,
            sub_agent_calls=self.sub_agent_calls.copy(),
            parallel_searches=len(search_queries),
            sequential_time_estimate=sequential_estimate
        )


def run_research(
    question: str,
    model: str = None,
    max_iterations: int = 10,
    verbose: bool = True,
    max_workers: int = 4
) -> ResearchResult:
    """
    Convenience function to run research on a question.
    """
    agent = ResearchAgentV4(
        model=model,
        max_iterations=max_iterations,
        verbose=verbose,
        max_workers=max_workers
    )
    return agent.research(question)
