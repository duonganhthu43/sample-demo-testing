"""
Research Agent
Responsible for gathering information from various sources
Uses agentic architecture where LLM decides which research tools to invoke
"""

import time
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..utils.config import get_config
from ..utils.prompts import RESEARCH_AGENT_SYSTEM, get_research_prompt
from ..tools import WebSearchTool, DataExtractor
from .research_tools import RESEARCH_TOOL_DEFINITIONS, ResearchToolExecutor



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
    """

    def __init__(self, config: Optional[Any] = None, max_iterations: int = 10):
        self.config = config or get_config()
        self.llm_client = self.config.get_llm_client(label="research_agent")
        self.llm_params = self.config.get_llm_params()
        self.max_iterations = max_iterations

        # Tools
        self.search_tool = WebSearchTool()
        self.data_extractor = DataExtractor()

        # Tool executor for agentic loop
        self.tool_executor = ResearchToolExecutor(self.search_tool, self.data_extractor)

        print(f"ResearchAgent initialized (agentic mode, max_iterations: {max_iterations})")

    def research_company(self, company_name: str, depth: str = "standard") -> ResearchResult:
        """
        Research a company comprehensively using agentic approach

        Args:
            company_name: Name of the company to research
            depth: Research depth (quick, standard, deep)

        Returns:
            ResearchResult with company information
        """
        start_time = time.time()
        print(f"\nStarting: ResearchAgent - Researching company: {company_name} (depth: {depth})")

        # Clear previous context
        self.tool_executor.clear_context()

        # Build research prompt
        prompt = f"""Research the company: {company_name}

You have access to research tools via function calling. Your goal is to gather comprehensive information about this company.

Recommended approach:
1. Search for company information (overview, products, business model)
2. Extract content from relevant URLs
3. Extract structured company data (founded, headquarters, employees, revenue)
4. Search for additional specific information if needed

Depth level: {depth}
- quick: 2-3 searches, extract 1-2 URLs
- standard: 3-4 searches, extract 3-5 URLs
- deep: 5+ searches, extract 5+ URLs, gather detailed metrics

When you have sufficient information, provide a final summary of your findings."""

        # Run agentic loop
        result_data = self._run_agentic_research(
            topic=company_name,
            research_type="company",
            prompt=prompt,
            depth=depth
        )

        duration = time.time() - start_time
        print(f"Complete: ResearchAgent - {duration:.2f}s\n")

        return result_data

    def research_market(self, market_name: str, depth: str = "standard") -> ResearchResult:
        """
        Research a market or industry using agentic approach

        Args:
            market_name: Name of the market/industry
            depth: Research depth

        Returns:
            ResearchResult with market information
        """
        start_time = time.time()
        print(f"\nStarting: ResearchAgent - Researching market: {market_name} (depth: {depth})")

        # Clear previous context
        self.tool_executor.clear_context()

        # Build research prompt
        prompt = f"""Research the market/industry: {market_name}

You have access to research tools via function calling. Your goal is to gather comprehensive market intelligence.

Recommended approach:
1. Search for market size and growth data
2. Search for industry trends and dynamics
3. Search for market leaders and key players
4. Extract content from relevant sources
5. Extract key metrics (market size, growth rate, etc.)

Depth level: {depth}
- quick: Focus on market size and top trends
- standard: Include competitive landscape and growth drivers
- deep: Comprehensive analysis including segments, trends, and forecasts

When you have sufficient market intelligence, provide a final summary."""

        # Run agentic loop
        result_data = self._run_agentic_research(
            topic=market_name,
            research_type="market",
            prompt=prompt,
            depth=depth
        )

        duration = time.time() - start_time
        print(f"Complete: ResearchAgent - {duration:.2f}s\n")

        return result_data

    def research_competitors(self, company_name: str, industry: str, depth: str = "standard") -> ResearchResult:
        """
        Research competitors in an industry using agentic approach

        Args:
            company_name: Reference company
            industry: Industry to research
            depth: Research depth

        Returns:
            ResearchResult with competitor information
        """
        start_time = time.time()
        print(f"\nStarting: ResearchAgent - Researching competitors for {company_name} (depth: {depth})")

        # Clear previous context
        self.tool_executor.clear_context()

        # Build research prompt
        prompt = f"""Research competitors for: {company_name} in the {industry} industry

You have access to research tools via function calling. Your goal is to identify and analyze competitors.

Recommended approach:
1. Search for direct competitors of {company_name}
2. Search for {industry} market leaders and companies
3. Search for alternatives to {company_name}
4. Extract content from competitor websites and analysis
5. Extract key metrics and competitive positioning data

Depth level: {depth}
- quick: Identify top 3-5 competitors
- standard: Analyze 5-10 competitors with key differentiators
- deep: Comprehensive competitive landscape with detailed comparisons

When you have sufficient competitor intelligence, provide a final summary."""

        # Run agentic loop
        result_data = self._run_agentic_research(
            topic=f"Competitors of {company_name}",
            research_type="competitors",
            prompt=prompt,
            depth=depth,
            metadata={"company": company_name, "industry": industry}
        )

        duration = time.time() - start_time
        print(f"Complete: ResearchAgent - {duration:.2f}s\n")

        return result_data

    def _run_agentic_research(
        self,
        topic: str,
        research_type: str,
        prompt: str,
        depth: str = "standard",
        metadata: Optional[Dict[str, Any]] = None
    ) -> ResearchResult:
        """
        Run agentic research loop where LLM decides which tools to call

        Args:
            topic: Research topic
            research_type: Type of research (company, market, competitors)
            prompt: Initial research prompt for LLM
            depth: Research depth
            metadata: Additional metadata

        Returns:
            ResearchResult with accumulated findings
        """
        # Initialize conversation
        messages = [
            {
                "role": "system",
                "content": """You are an expert research agent with access to web search and data extraction tools.

Your role is to autonomously gather information by strategically using the available research tools.

STRATEGIC APPROACH:
1. Start with web searches to find relevant sources
2. Extract content from promising URLs to get detailed information
3. Use extraction tools to parse structured data when available
4. Gather sufficient information before concluding

DECISION-MAKING:
- Be strategic - each tool call should add value
- Extract content from only the most relevant sources
- When you have sufficient information, provide a comprehensive summary
- The tools and their descriptions are provided via function calling

Remember: Your summary will be used to generate research reports, so be thorough and accurate."""
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        # Track tool calls
        tool_calls_made = []
        sources_gathered = set()

        # Agentic loop
        iteration = 0
        final_summary = ""
        findings = []

        while iteration < self.max_iterations:
            iteration += 1

            try:
                # Call LLM with research tools
                response = self.llm_client.chat.completions.create(
                    messages=messages,
                    tools=RESEARCH_TOOL_DEFINITIONS,
                    tool_choice="auto",
                    **self.llm_params
                )

                assistant_message = response.choices[0].message

                # Add assistant message to conversation
                messages.append({
                    "role": "assistant",
                    "content": assistant_message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in (assistant_message.tool_calls or [])
                    ] if assistant_message.tool_calls else None
                })

                # Check if LLM wants to call tools
                if assistant_message.tool_calls:
                    num_tools = len(assistant_message.tool_calls)
                    print(f"  🤖 LLM requested {num_tools} tool(s) in iteration {iteration}")

                    # Execute tool calls in parallel
                    def execute_single_tool(tool_call):
                        """Execute a single tool call"""
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments)

                        # Execute tool
                        tool_result = self.tool_executor.execute_tool(
                            tool_name=function_name,
                            arguments=function_args
                        )

                        return {
                            "tool_call_id": tool_call.id,
                            "function_name": function_name,
                            "function_args": function_args,
                            "result": tool_result
                        }

                    # Execute in parallel if multiple tools
                    tool_results = []
                    if num_tools > 1:
                        with ThreadPoolExecutor(max_workers=num_tools) as executor:
                            future_to_tool = {
                                executor.submit(execute_single_tool, tc): tc
                                for tc in assistant_message.tool_calls
                            }

                            for future in as_completed(future_to_tool):
                                try:
                                    tool_data = future.result()
                                    tool_results.append(tool_data)
                                    print(f"     ✅ {tool_data['function_name']}")
                                except Exception as e:
                                    print(f"     ❌ Error: {str(e)}")
                    else:
                        # Single tool
                        for tc in assistant_message.tool_calls:
                            tool_data = execute_single_tool(tc)
                            tool_results.append(tool_data)
                            print(f"     ✅ {tool_data['function_name']}")

                    # Add tool results to conversation and track
                    for tool_data in tool_results:
                        tool_calls_made.append(tool_data["function_name"])

                        # Track sources
                        if "url" in tool_data["function_args"]:
                            sources_gathered.add(tool_data["function_args"]["url"])
                        if "results" in tool_data["result"]:
                            for r in tool_data["result"]["results"]:
                                sources_gathered.add(r["url"])

                        # Add to conversation
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_data["tool_call_id"],
                            "name": tool_data["function_name"],
                            "content": json.dumps(tool_data["result"])
                        })

                else:
                    # No more tool calls - LLM is done
                    print(f"  ✅ Research complete after {iteration} iteration(s)")
                    if assistant_message.content:
                        final_summary = assistant_message.content
                    break

            except Exception as e:
                print(f"  ❌ Error in iteration {iteration}: {str(e)}")
                break

        # Build result from accumulated context
        context = self.tool_executor.get_context()

        # Extract findings from context
        for item in context.get("structured_data", []):
            findings.append(item)

        # Create result
        result = ResearchResult(
            topic=topic,
            research_type=research_type,
            summary=final_summary or "Research completed",
            findings=findings,
            sources=list(sources_gathered),
            confidence=0.8 if len(sources_gathered) >= 3 else 0.6,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            metadata={
                "depth": depth,
                "iterations": iteration,
                "tool_calls": tool_calls_made,
                "num_sources": len(sources_gathered),
                **(metadata or {})
            }
        )

        return result
