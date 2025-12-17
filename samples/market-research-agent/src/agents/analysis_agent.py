"""
Analysis Agent
Performs strategic analysis on research data
Uses agentic architecture where LLM decides which analytical tools to invoke
"""

import time
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..utils.config import get_config
from ..utils.prompts import ANALYSIS_AGENT_SYSTEM
from ..tools import create_swot_visualization
from .analysis_tools import ANALYSIS_TOOL_DEFINITIONS, AnalysisToolExecutor


@dataclass
class AnalysisResult:
    """Analysis result data structure"""
    analysis_type: str
    subject: str
    insights: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    confidence: float = 0.0
    timestamp: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "analysis_type": self.analysis_type,
            "subject": self.subject,
            "insights": self.insights,
            "recommendations": self.recommendations,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }


class AnalysisAgent:
    """
    Agent specialized in strategic business analysis
    Uses agentic approach where LLM decides which analytical tools to use
    """

    def __init__(self, config: Optional[Any] = None, max_iterations: int = 10):
        self.config = config or get_config()
        self.llm_client = self.config.get_llm_client(label="analysis_agent")
        self.llm_params = self.config.get_llm_params()
        self.max_iterations = max_iterations

        print(f"AnalysisAgent initialized (agentic mode, max_iterations: {max_iterations})")

    def perform_swot_analysis(self, company_name: str, research_data: Dict[str, Any]) -> AnalysisResult:
        """
        Perform SWOT analysis using agentic approach

        Args:
            company_name: Company to analyze
            research_data: Research data from ResearchAgent

        Returns:
            AnalysisResult with SWOT insights
        """
        start_time = time.time()
        print(f"\nStarting: AnalysisAgent - SWOT analysis for {company_name}")

        # Build analysis prompt
        prompt = f"""Perform a comprehensive SWOT analysis for: {company_name}

You have access to analytical tools via function calling. Your goal is to identify strengths, weaknesses, opportunities, and threats.

Recommended approach:
1. Identify company strengths (internal positive factors)
2. Identify company weaknesses (internal negative factors)
3. Identify market opportunities (external positive factors)
4. Identify threats (external negative factors)
5. Generate strategic recommendations based on SWOT findings

When you have completed all components, provide a final strategic summary."""

        # Run agentic analysis
        result_data = self._run_agentic_analysis(
            analysis_type="swot",
            subject=company_name,
            research_data=research_data,
            prompt=prompt
        )

        # Create SWOT visualization
        context = result_data.metadata.get("analysis_context", {})
        viz = create_swot_visualization({
            "strengths": [s.get("strength", s) if isinstance(s, dict) else s for s in context.get("strengths", [])],
            "weaknesses": [w.get("weakness", w) if isinstance(w, dict) else w for w in context.get("weaknesses", [])],
            "opportunities": [o.get("opportunity", o) if isinstance(o, dict) else o for o in context.get("opportunities", [])],
            "threats": [t.get("threat", t) if isinstance(t, dict) else t for t in context.get("threats", [])]
        })

        result_data.insights["visualization"] = viz

        duration = time.time() - start_time
        print(f"Complete: AnalysisAgent - {duration:.2f}s\n")

        return result_data

    def perform_competitive_analysis(
        self,
        company_name: str,
        research_data: Dict[str, Any],
        competitor_data: Optional[Dict[str, Any]] = None
    ) -> AnalysisResult:
        """
        Perform competitive analysis using agentic approach

        Args:
            company_name: Company to analyze
            research_data: Research data
            competitor_data: Optional competitor research data

        Returns:
            AnalysisResult with competitive insights
        """
        start_time = time.time()
        print(f"\nStarting: AnalysisAgent - Competitive analysis for {company_name}")

        # Merge research data with competitor data
        combined_data = research_data.copy()
        if competitor_data:
            combined_data["competitor_data"] = competitor_data

        # Build analysis prompt
        prompt = f"""Perform a comprehensive competitive analysis for: {company_name}

You have access to analytical tools via function calling. Your goal is to analyze competitive positioning and dynamics.

Recommended approach:
1. Analyze competitive positioning (where the company stands relative to competitors)
2. Identify competitive advantages and gaps
3. Identify market threats from competitors
4. Identify market opportunities based on competitive landscape
5. Generate strategic recommendations for competitive strategy

When you have completed the analysis, provide a final competitive summary."""

        # Run agentic analysis
        result_data = self._run_agentic_analysis(
            analysis_type="competitive",
            subject=company_name,
            research_data=combined_data,
            prompt=prompt
        )

        duration = time.time() - start_time
        print(f"Complete: AnalysisAgent - {duration:.2f}s\n")

        return result_data

    def perform_trend_analysis(
        self,
        company_name: str,
        industry: str,
        research_data: Dict[str, Any]
    ) -> AnalysisResult:
        """
        Perform trend analysis using agentic approach

        Args:
            company_name: Company to analyze
            industry: Industry context
            research_data: Research data

        Returns:
            AnalysisResult with trend insights
        """
        start_time = time.time()
        print(f"\nStarting: AnalysisAgent - Trend analysis for {company_name} in {industry}")

        # Build analysis prompt
        prompt = f"""Perform a comprehensive trend analysis for: {company_name} in the {industry} industry

You have access to analytical tools via function calling. Your goal is to identify and analyze market trends.

Recommended approach:
1. Identify current market trends (technology, consumer behavior, regulations)
2. Identify opportunities emerging from these trends
3. Identify threats from negative trends
4. Generate strategic recommendations for trend adaptation

Focus on trends that impact {industry} and {company_name}'s position.

When you have completed the analysis, provide a final trend summary."""

        # Run agentic analysis
        result_data = self._run_agentic_analysis(
            analysis_type="trends",
            subject=f"{company_name} in {industry}",
            research_data=research_data,
            prompt=prompt,
            metadata={"industry": industry}
        )

        duration = time.time() - start_time
        print(f"Complete: AnalysisAgent - {duration:.2f}s\n")

        return result_data

    def _run_agentic_analysis(
        self,
        analysis_type: str,
        subject: str,
        research_data: Dict[str, Any],
        prompt: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AnalysisResult:
        """
        Run agentic analysis loop where LLM decides which analytical tools to call

        Args:
            analysis_type: Type of analysis (swot, competitive, trends)
            subject: Subject of analysis
            research_data: Research data to analyze
            prompt: Initial analysis prompt for LLM
            metadata: Additional metadata

        Returns:
            AnalysisResult with accumulated insights
        """
        # Initialize tool executor with research data
        tool_executor = AnalysisToolExecutor(research_data, self.llm_client, self.llm_params)

        # Initialize conversation
        messages = [
            {
                "role": "system",
                "content": """You are an expert strategic business analyst with access to analytical tools.

Your role is to autonomously perform analysis by strategically using the available analytical tools.

STRATEGIC APPROACH:
1. Use tools to systematically gather analytical insights
2. Build analysis progressively from individual components
3. Synthesize findings into comprehensive strategic insights
4. Generate actionable recommendations

DECISION-MAKING:
- Be thorough - use tools to analyze all relevant dimensions
- Each tool call should uncover specific insights
- When you have sufficient insights, provide a comprehensive summary
- The tools and their descriptions are provided via function calling

Remember: Your analysis will inform strategic decisions, so be rigorous and insightful."""
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        # Track tool calls
        tool_calls_made = []

        # Agentic loop
        iteration = 0
        final_summary = ""

        while iteration < self.max_iterations:
            iteration += 1

            try:
                # Call LLM with analysis tools
                response = self.llm_client.chat.completions.create(
                    messages=messages,
                    tools=ANALYSIS_TOOL_DEFINITIONS,
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
                    print(f"  🤖 LLM requested {num_tools} analytical tool(s) in iteration {iteration}")

                    # Execute tool calls in parallel
                    def execute_single_tool(tool_call):
                        """Execute a single tool call"""
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments)

                        # Execute tool
                        tool_result = tool_executor.execute_tool(
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

                        # Add to conversation
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_data["tool_call_id"],
                            "name": tool_data["function_name"],
                            "content": json.dumps(tool_data["result"])
                        })

                else:
                    # No more tool calls - LLM is done
                    print(f"  ✅ Analysis complete after {iteration} iteration(s)")
                    if assistant_message.content:
                        final_summary = assistant_message.content
                    break

            except Exception as e:
                print(f"  ❌ Error in iteration {iteration}: {str(e)}")
                break

        # Build result from accumulated context
        analysis_context = tool_executor.get_context()

        # Build insights from analysis context
        insights = {}
        if analysis_context.get("strengths"):
            insights["strengths"] = analysis_context["strengths"]
        if analysis_context.get("weaknesses"):
            insights["weaknesses"] = analysis_context["weaknesses"]
        if analysis_context.get("opportunities"):
            insights["opportunities"] = analysis_context["opportunities"]
        if analysis_context.get("threats"):
            insights["threats"] = analysis_context["threats"]
        if analysis_context.get("competitive_insights"):
            insights["competitive_insights"] = analysis_context["competitive_insights"]
        if analysis_context.get("trends"):
            insights["trends"] = analysis_context["trends"]

        # Add summary
        if final_summary:
            insights["summary"] = final_summary

        # Extract recommendations
        recommendations = []
        for rec in analysis_context.get("recommendations", []):
            if isinstance(rec, dict):
                recommendations.append(rec.get("recommendation", str(rec)))
            else:
                recommendations.append(str(rec))

        # Create result
        result = AnalysisResult(
            analysis_type=analysis_type,
            subject=subject,
            insights=insights,
            recommendations=recommendations,
            confidence=0.8 if len(tool_calls_made) >= 3 else 0.6,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            metadata={
                "iterations": iteration,
                "tool_calls": tool_calls_made,
                "analysis_context": analysis_context,
                **(metadata or {})
            }
        )

        return result
