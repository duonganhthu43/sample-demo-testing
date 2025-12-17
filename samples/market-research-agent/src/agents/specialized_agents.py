"""
Specialized Sub-Agents
Deep-dive experts for specific research domains
All use agentic architecture where LLM decides which analytical tools to invoke
"""

import time
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..utils.config import get_config
from ..utils.prompts import (
    FINANCIAL_AGENT_SYSTEM,
    TECHNOLOGY_AGENT_SYSTEM,
    MARKET_SIZING_AGENT_SYSTEM,
    SENTIMENT_AGENT_SYSTEM,
    REGULATORY_AGENT_SYSTEM
)
from .specialized_tools import (
    FINANCIAL_TOOL_DEFINITIONS,
    TECHNOLOGY_TOOL_DEFINITIONS,
    MARKET_SIZING_TOOL_DEFINITIONS,
    SENTIMENT_TOOL_DEFINITIONS,
    REGULATORY_TOOL_DEFINITIONS,
    FinancialToolExecutor,
    TechnologyToolExecutor,
    MarketSizingToolExecutor,
    SentimentToolExecutor,
    RegulatoryToolExecutor
)


@dataclass
class SpecializedResult:
    """Result from specialized agent"""
    agent_type: str
    company_name: str
    findings: Dict[str, Any] = field(default_factory=dict)
    insights: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    confidence: float = 0.8
    sources: List[str] = field(default_factory=list)
    timestamp: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "agent_type": self.agent_type,
            "company_name": self.company_name,
            "findings": self.findings,
            "insights": self.insights,
            "recommendations": self.recommendations,
            "confidence": self.confidence,
            "sources": self.sources,
            "timestamp": self.timestamp,
            "metadata": self.metadata
        }


class FinancialAgent:
    """
    Specialized agent for financial analysis
    Uses agentic architecture where LLM decides which financial tools to invoke
    """

    def __init__(self, config: Optional[Any] = None, max_iterations: int = 8):
        self.config = config or get_config()
        self.llm_client = self.config.get_llm_client(label="financial_agent")
        self.llm_params = self.config.get_llm_params()
        self.max_iterations = max_iterations

        print(f"FinancialAgent initialized (agentic mode, max_iterations: {max_iterations})")

    def analyze_financials(
        self,
        company_name: str,
        context: Dict[str, Any]
    ) -> SpecializedResult:
        """
        Perform deep financial analysis using agentic approach

        Args:
            company_name: Company to analyze
            context: Research context and data

        Returns:
            Financial analysis results
        """
        start_time = time.time()
        print(f"\nStarting: FinancialAgent - Analyzing {company_name}")

        prompt = f"""Perform comprehensive financial analysis for: {company_name}

You have access to financial analysis tools via function calling. Your goal is to deeply analyze financial aspects.

Recommended approach:
1. Analyze revenue model and monetization strategy
2. Analyze funding history and capital structure
3. Assess financial health and sustainability
4. Identify financial risks and vulnerabilities

When you have completed the analysis, provide a final financial summary with insights and recommendations."""

        # Run agentic analysis
        result = self._run_agentic_analysis(
            company_name=company_name,
            context=context,
            prompt=prompt,
            agent_type="financial_analysis"
        )

        duration = time.time() - start_time
        print(f"Complete: FinancialAgent - {duration:.2f}s\n")

        return result

    def _run_agentic_analysis(
        self,
        company_name: str,
        context: Dict[str, Any],
        prompt: str,
        agent_type: str
    ) -> SpecializedResult:
        """Run agentic financial analysis loop"""

        # Initialize tool executor
        tool_executor = FinancialToolExecutor(context, self.llm_client, self.llm_params)

        # Initialize conversation
        messages = [
            {
                "role": "system",
                "content": FINANCIAL_AGENT_SYSTEM + "\n\nYou have access to specialized financial analysis tools. Use them strategically to build comprehensive insights."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        # Agentic loop
        tool_calls_made = []
        iteration = 0
        final_summary = ""

        while iteration < self.max_iterations:
            iteration += 1

            try:
                response = self.llm_client.chat.completions.create(
                    messages=messages,
                    tools=FINANCIAL_TOOL_DEFINITIONS,
                    tool_choice="auto",
                    **self.llm_params
                )

                assistant_message = response.choices[0].message

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

                if assistant_message.tool_calls:
                    num_tools = len(assistant_message.tool_calls)
                    print(f"  🤖 LLM requested {num_tools} financial tool(s) in iteration {iteration}")

                    # Execute tools in parallel
                    tool_results = self._execute_tools_parallel(assistant_message.tool_calls, tool_executor)

                    # Add results to conversation
                    for tool_data in tool_results:
                        tool_calls_made.append(tool_data["function_name"])
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_data["tool_call_id"],
                            "name": tool_data["function_name"],
                            "content": json.dumps(tool_data["result"])
                        })

                else:
                    print(f"  ✅ Analysis complete after {iteration} iteration(s)")
                    if assistant_message.content:
                        final_summary = assistant_message.content
                    break

            except Exception as e:
                print(f"  ❌ Error in iteration {iteration}: {str(e)}")
                break

        # Build result
        findings = tool_executor.get_findings()

        return SpecializedResult(
            agent_type=agent_type,
            company_name=company_name,
            findings=findings,
            insights=[final_summary] if final_summary else [],
            recommendations=[],
            confidence=0.85 if len(tool_calls_made) >= 3 else 0.7,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            metadata={
                "iterations": iteration,
                "tool_calls": tool_calls_made,
                "duration_seconds": time.time() - time.time()
            }
        )

    def _execute_tools_parallel(self, tool_calls, tool_executor):
        """Execute tools in parallel"""
        def execute_single_tool(tool_call):
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            tool_result = tool_executor.execute_tool(function_name, function_args)
            return {
                "tool_call_id": tool_call.id,
                "function_name": function_name,
                "function_args": function_args,
                "result": tool_result
            }

        tool_results = []
        num_tools = len(tool_calls)

        if num_tools > 1:
            with ThreadPoolExecutor(max_workers=num_tools) as executor:
                future_to_tool = {
                    executor.submit(execute_single_tool, tc): tc
                    for tc in tool_calls
                }
                for future in as_completed(future_to_tool):
                    try:
                        tool_data = future.result()
                        tool_results.append(tool_data)
                        print(f"     ✅ {tool_data['function_name']}")
                    except Exception as e:
                        print(f"     ❌ Error: {str(e)}")
        else:
            for tc in tool_calls:
                tool_data = execute_single_tool(tc)
                tool_results.append(tool_data)
                print(f"     ✅ {tool_data['function_name']}")

        return tool_results


class TechnologyAgent:
    """
    Specialized agent for technology analysis
    Uses agentic architecture where LLM decides which technology tools to invoke
    """

    def __init__(self, config: Optional[Any] = None, max_iterations: int = 8):
        self.config = config or get_config()
        self.llm_client = self.config.get_llm_client(label="technology_agent")
        self.llm_params = self.config.get_llm_params()
        self.max_iterations = max_iterations

        print(f"TechnologyAgent initialized (agentic mode, max_iterations: {max_iterations})")

    def analyze_technology(
        self,
        company_name: str,
        context: Dict[str, Any]
    ) -> SpecializedResult:
        """
        Perform deep technology analysis using agentic approach

        Args:
            company_name: Company to analyze
            context: Research context and data

        Returns:
            Technology analysis results
        """
        start_time = time.time()
        print(f"\nStarting: TechnologyAgent - Analyzing {company_name}")

        prompt = f"""Perform comprehensive technology analysis for: {company_name}

You have access to technology analysis tools via function calling. Your goal is to deeply analyze technical aspects.

Recommended approach:
1. Analyze technology stack and infrastructure
2. Evaluate innovation capability and R&D
3. Assess intellectual property portfolio
4. Identify technical advantages and differentiation

When you have completed the analysis, provide a final technology summary with insights."""

        # Run agentic analysis
        result = self._run_agentic_analysis(
            company_name=company_name,
            context=context,
            prompt=prompt,
            agent_type="technology_analysis"
        )

        duration = time.time() - start_time
        print(f"Complete: TechnologyAgent - {duration:.2f}s\n")

        return result

    def _run_agentic_analysis(
        self,
        company_name: str,
        context: Dict[str, Any],
        prompt: str,
        agent_type: str
    ) -> SpecializedResult:
        """Run agentic technology analysis loop"""

        tool_executor = TechnologyToolExecutor(context, self.llm_client, self.llm_params)

        messages = [
            {
                "role": "system",
                "content": TECHNOLOGY_AGENT_SYSTEM + "\n\nYou have access to specialized technology analysis tools. Use them strategically to build comprehensive insights."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        tool_calls_made = []
        iteration = 0
        final_summary = ""

        while iteration < self.max_iterations:
            iteration += 1

            try:
                response = self.llm_client.chat.completions.create(
                    messages=messages,
                    tools=TECHNOLOGY_TOOL_DEFINITIONS,
                    tool_choice="auto",
                    **self.llm_params
                )

                assistant_message = response.choices[0].message

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

                if assistant_message.tool_calls:
                    num_tools = len(assistant_message.tool_calls)
                    print(f"  🤖 LLM requested {num_tools} technology tool(s) in iteration {iteration}")

                    tool_results = self._execute_tools_parallel(assistant_message.tool_calls, tool_executor)

                    for tool_data in tool_results:
                        tool_calls_made.append(tool_data["function_name"])
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_data["tool_call_id"],
                            "name": tool_data["function_name"],
                            "content": json.dumps(tool_data["result"])
                        })

                else:
                    print(f"  ✅ Analysis complete after {iteration} iteration(s)")
                    if assistant_message.content:
                        final_summary = assistant_message.content
                    break

            except Exception as e:
                print(f"  ❌ Error in iteration {iteration}: {str(e)}")
                break

        findings = tool_executor.get_findings()

        return SpecializedResult(
            agent_type=agent_type,
            company_name=company_name,
            findings=findings,
            insights=[final_summary] if final_summary else [],
            recommendations=[],
            confidence=0.85 if len(tool_calls_made) >= 3 else 0.7,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            metadata={
                "iterations": iteration,
                "tool_calls": tool_calls_made
            }
        )

    def _execute_tools_parallel(self, tool_calls, tool_executor):
        """Execute tools in parallel"""
        def execute_single_tool(tool_call):
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            tool_result = tool_executor.execute_tool(function_name, function_args)
            return {
                "tool_call_id": tool_call.id,
                "function_name": function_name,
                "function_args": function_args,
                "result": tool_result
            }

        tool_results = []
        num_tools = len(tool_calls)

        if num_tools > 1:
            with ThreadPoolExecutor(max_workers=num_tools) as executor:
                future_to_tool = {
                    executor.submit(execute_single_tool, tc): tc
                    for tc in tool_calls
                }
                for future in as_completed(future_to_tool):
                    try:
                        tool_data = future.result()
                        tool_results.append(tool_data)
                        print(f"     ✅ {tool_data['function_name']}")
                    except Exception as e:
                        print(f"     ❌ Error: {str(e)}")
        else:
            for tc in tool_calls:
                tool_data = execute_single_tool(tc)
                tool_results.append(tool_data)
                print(f"     ✅ {tool_data['function_name']}")

        return tool_results


class MarketSizingAgent:
    """
    Specialized agent for market sizing analysis
    Uses agentic architecture where LLM decides which market sizing tools to invoke
    """

    def __init__(self, config: Optional[Any] = None, max_iterations: int = 10):
        self.config = config or get_config()
        self.llm_client = self.config.get_llm_client(label="market_sizing_agent")
        self.llm_params = self.config.get_llm_params()
        self.max_iterations = max_iterations

        print(f"MarketSizingAgent initialized (agentic mode, max_iterations: {max_iterations})")

    def analyze_market_size(
        self,
        company_name: str,
        industry: str,
        context: Dict[str, Any]
    ) -> SpecializedResult:
        """
        Perform market sizing analysis using agentic approach

        Args:
            company_name: Company to analyze
            industry: Industry context
            context: Research context and data

        Returns:
            Market sizing results
        """
        start_time = time.time()
        print(f"\nStarting: MarketSizingAgent - Analyzing {company_name} in {industry}")

        prompt = f"""Perform comprehensive market sizing analysis for: {company_name} in {industry}

You have access to market sizing tools via function calling. Your goal is to estimate market opportunity.

Recommended approach:
1. Calculate TAM (Total Addressable Market)
2. Calculate SAM (Serviceable Addressable Market)
3. Calculate SOM (Serviceable Obtainable Market)
4. Analyze market segments
5. Project market growth

When you have completed the analysis, provide a final market sizing summary."""

        # Run agentic analysis
        result = self._run_agentic_analysis(
            company_name=company_name,
            context=context,
            prompt=prompt,
            agent_type="market_sizing"
        )

        duration = time.time() - start_time
        print(f"Complete: MarketSizingAgent - {duration:.2f}s\n")

        return result

    def _run_agentic_analysis(
        self,
        company_name: str,
        context: Dict[str, Any],
        prompt: str,
        agent_type: str
    ) -> SpecializedResult:
        """Run agentic market sizing loop"""

        tool_executor = MarketSizingToolExecutor(context, self.llm_client, self.llm_params)

        messages = [
            {
                "role": "system",
                "content": MARKET_SIZING_AGENT_SYSTEM + "\n\nYou have access to specialized market sizing tools. Use them strategically to estimate market opportunity."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        tool_calls_made = []
        iteration = 0
        final_summary = ""

        while iteration < self.max_iterations:
            iteration += 1

            try:
                response = self.llm_client.chat.completions.create(
                    messages=messages,
                    tools=MARKET_SIZING_TOOL_DEFINITIONS,
                    tool_choice="auto",
                    **self.llm_params
                )

                assistant_message = response.choices[0].message

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

                if assistant_message.tool_calls:
                    num_tools = len(assistant_message.tool_calls)
                    print(f"  🤖 LLM requested {num_tools} market sizing tool(s) in iteration {iteration}")

                    tool_results = self._execute_tools_parallel(assistant_message.tool_calls, tool_executor)

                    for tool_data in tool_results:
                        tool_calls_made.append(tool_data["function_name"])
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_data["tool_call_id"],
                            "name": tool_data["function_name"],
                            "content": json.dumps(tool_data["result"])
                        })

                else:
                    print(f"  ✅ Analysis complete after {iteration} iteration(s)")
                    if assistant_message.content:
                        final_summary = assistant_message.content
                    break

            except Exception as e:
                print(f"  ❌ Error in iteration {iteration}: {str(e)}")
                break

        findings = tool_executor.get_findings()

        return SpecializedResult(
            agent_type=agent_type,
            company_name=company_name,
            findings=findings,
            insights=[final_summary] if final_summary else [],
            recommendations=[],
            confidence=0.75 if len(tool_calls_made) >= 3 else 0.6,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            metadata={
                "iterations": iteration,
                "tool_calls": tool_calls_made
            }
        )

    def _execute_tools_parallel(self, tool_calls, tool_executor):
        """Execute tools in parallel"""
        def execute_single_tool(tool_call):
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            tool_result = tool_executor.execute_tool(function_name, function_args)
            return {
                "tool_call_id": tool_call.id,
                "function_name": function_name,
                "function_args": function_args,
                "result": tool_result
            }

        tool_results = []
        num_tools = len(tool_calls)

        if num_tools > 1:
            with ThreadPoolExecutor(max_workers=num_tools) as executor:
                future_to_tool = {
                    executor.submit(execute_single_tool, tc): tc
                    for tc in tool_calls
                }
                for future in as_completed(future_to_tool):
                    try:
                        tool_data = future.result()
                        tool_results.append(tool_data)
                        print(f"     ✅ {tool_data['function_name']}")
                    except Exception as e:
                        print(f"     ❌ Error: {str(e)}")
        else:
            for tc in tool_calls:
                tool_data = execute_single_tool(tc)
                tool_results.append(tool_data)
                print(f"     ✅ {tool_data['function_name']}")

        return tool_results


class SentimentAgent:
    """
    Specialized agent for sentiment analysis
    Uses agentic architecture where LLM decides which sentiment tools to invoke
    """

    def __init__(self, config: Optional[Any] = None, max_iterations: int = 8):
        self.config = config or get_config()
        self.llm_client = self.config.get_llm_client(label="sentiment_agent")
        self.llm_params = self.config.get_llm_params()
        self.max_iterations = max_iterations

        print(f"SentimentAgent initialized (agentic mode, max_iterations: {max_iterations})")

    def analyze_sentiment(
        self,
        company_name: str,
        context: Dict[str, Any]
    ) -> SpecializedResult:
        """
        Perform sentiment analysis using agentic approach

        Args:
            company_name: Company to analyze
            context: Research context and data

        Returns:
            Sentiment analysis results
        """
        start_time = time.time()
        print(f"\nStarting: SentimentAgent - Analyzing {company_name}")

        prompt = f"""Perform comprehensive sentiment analysis for: {company_name}

You have access to sentiment analysis tools via function calling. Your goal is to analyze customer and brand sentiment.

Recommended approach:
1. Analyze overall customer sentiment
2. Analyze brand perception and reputation
3. Identify key sentiment themes
4. Compare with competitor sentiment

When you have completed the analysis, provide a final sentiment summary."""

        # Run agentic analysis
        result = self._run_agentic_analysis(
            company_name=company_name,
            context=context,
            prompt=prompt,
            agent_type="sentiment_analysis"
        )

        duration = time.time() - start_time
        print(f"Complete: SentimentAgent - {duration:.2f}s\n")

        return result

    def _run_agentic_analysis(
        self,
        company_name: str,
        context: Dict[str, Any],
        prompt: str,
        agent_type: str
    ) -> SpecializedResult:
        """Run agentic sentiment analysis loop"""

        tool_executor = SentimentToolExecutor(context, self.llm_client, self.llm_params)

        messages = [
            {
                "role": "system",
                "content": SENTIMENT_AGENT_SYSTEM + "\n\nYou have access to specialized sentiment analysis tools. Use them strategically to analyze sentiment and perception."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        tool_calls_made = []
        iteration = 0
        final_summary = ""

        while iteration < self.max_iterations:
            iteration += 1

            try:
                response = self.llm_client.chat.completions.create(
                    messages=messages,
                    tools=SENTIMENT_TOOL_DEFINITIONS,
                    tool_choice="auto",
                    **self.llm_params
                )

                assistant_message = response.choices[0].message

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

                if assistant_message.tool_calls:
                    num_tools = len(assistant_message.tool_calls)
                    print(f"  🤖 LLM requested {num_tools} sentiment tool(s) in iteration {iteration}")

                    tool_results = self._execute_tools_parallel(assistant_message.tool_calls, tool_executor)

                    for tool_data in tool_results:
                        tool_calls_made.append(tool_data["function_name"])
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_data["tool_call_id"],
                            "name": tool_data["function_name"],
                            "content": json.dumps(tool_data["result"])
                        })

                else:
                    print(f"  ✅ Analysis complete after {iteration} iteration(s)")
                    if assistant_message.content:
                        final_summary = assistant_message.content
                    break

            except Exception as e:
                print(f"  ❌ Error in iteration {iteration}: {str(e)}")
                break

        findings = tool_executor.get_findings()

        return SpecializedResult(
            agent_type=agent_type,
            company_name=company_name,
            findings=findings,
            insights=[final_summary] if final_summary else [],
            recommendations=[],
            confidence=0.80 if len(tool_calls_made) >= 3 else 0.65,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            metadata={
                "iterations": iteration,
                "tool_calls": tool_calls_made
            }
        )

    def _execute_tools_parallel(self, tool_calls, tool_executor):
        """Execute tools in parallel"""
        def execute_single_tool(tool_call):
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            tool_result = tool_executor.execute_tool(function_name, function_args)
            return {
                "tool_call_id": tool_call.id,
                "function_name": function_name,
                "function_args": function_args,
                "result": tool_result
            }

        tool_results = []
        num_tools = len(tool_calls)

        if num_tools > 1:
            with ThreadPoolExecutor(max_workers=num_tools) as executor:
                future_to_tool = {
                    executor.submit(execute_single_tool, tc): tc
                    for tc in tool_calls
                }
                for future in as_completed(future_to_tool):
                    try:
                        tool_data = future.result()
                        tool_results.append(tool_data)
                        print(f"     ✅ {tool_data['function_name']}")
                    except Exception as e:
                        print(f"     ❌ Error: {str(e)}")
        else:
            for tc in tool_calls:
                tool_data = execute_single_tool(tc)
                tool_results.append(tool_data)
                print(f"     ✅ {tool_data['function_name']}")

        return tool_results


class RegulatoryAgent:
    """
    Specialized agent for regulatory analysis
    Uses agentic architecture where LLM decides which regulatory tools to invoke
    """

    def __init__(self, config: Optional[Any] = None, max_iterations: int = 8):
        self.config = config or get_config()
        self.llm_client = self.config.get_llm_client(label="regulatory_agent")
        self.llm_params = self.config.get_llm_params()
        self.max_iterations = max_iterations

        print(f"RegulatoryAgent initialized (agentic mode, max_iterations: {max_iterations})")

    def analyze_regulatory(
        self,
        company_name: str,
        industry: str,
        context: Dict[str, Any]
    ) -> SpecializedResult:
        """
        Perform regulatory analysis using agentic approach

        Args:
            company_name: Company to analyze
            industry: Industry context
            context: Research context and data

        Returns:
            Regulatory analysis results
        """
        start_time = time.time()
        print(f"\nStarting: RegulatoryAgent - Analyzing {company_name} in {industry}")

        prompt = f"""Perform comprehensive regulatory analysis for: {company_name} in {industry}

You have access to regulatory analysis tools via function calling. Your goal is to analyze regulatory compliance.

Recommended approach:
1. Identify key regulations and requirements
2. Assess current compliance status
3. Identify regulatory risks and challenges
4. Analyze recent and pending policy changes

When you have completed the analysis, provide a final regulatory summary."""

        # Run agentic analysis
        result = self._run_agentic_analysis(
            company_name=company_name,
            context=context,
            prompt=prompt,
            agent_type="regulatory_analysis"
        )

        duration = time.time() - start_time
        print(f"Complete: RegulatoryAgent - {duration:.2f}s\n")

        return result

    def _run_agentic_analysis(
        self,
        company_name: str,
        context: Dict[str, Any],
        prompt: str,
        agent_type: str
    ) -> SpecializedResult:
        """Run agentic regulatory analysis loop"""

        tool_executor = RegulatoryToolExecutor(context, self.llm_client, self.llm_params)

        messages = [
            {
                "role": "system",
                "content": REGULATORY_AGENT_SYSTEM + "\n\nYou have access to specialized regulatory analysis tools. Use them strategically to analyze compliance and risks."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        tool_calls_made = []
        iteration = 0
        final_summary = ""

        while iteration < self.max_iterations:
            iteration += 1

            try:
                response = self.llm_client.chat.completions.create(
                    messages=messages,
                    tools=REGULATORY_TOOL_DEFINITIONS,
                    tool_choice="auto",
                    **self.llm_params
                )

                assistant_message = response.choices[0].message

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

                if assistant_message.tool_calls:
                    num_tools = len(assistant_message.tool_calls)
                    print(f"  🤖 LLM requested {num_tools} regulatory tool(s) in iteration {iteration}")

                    tool_results = self._execute_tools_parallel(assistant_message.tool_calls, tool_executor)

                    for tool_data in tool_results:
                        tool_calls_made.append(tool_data["function_name"])
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_data["tool_call_id"],
                            "name": tool_data["function_name"],
                            "content": json.dumps(tool_data["result"])
                        })

                else:
                    print(f"  ✅ Analysis complete after {iteration} iteration(s)")
                    if assistant_message.content:
                        final_summary = assistant_message.content
                    break

            except Exception as e:
                print(f"  ❌ Error in iteration {iteration}: {str(e)}")
                break

        findings = tool_executor.get_findings()

        return SpecializedResult(
            agent_type=agent_type,
            company_name=company_name,
            findings=findings,
            insights=[final_summary] if final_summary else [],
            recommendations=[],
            confidence=0.80 if len(tool_calls_made) >= 3 else 0.65,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            metadata={
                "iterations": iteration,
                "tool_calls": tool_calls_made
            }
        )

    def _execute_tools_parallel(self, tool_calls, tool_executor):
        """Execute tools in parallel"""
        def execute_single_tool(tool_call):
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            tool_result = tool_executor.execute_tool(function_name, function_args)
            return {
                "tool_call_id": tool_call.id,
                "function_name": function_name,
                "function_args": function_args,
                "result": tool_result
            }

        tool_results = []
        num_tools = len(tool_calls)

        if num_tools > 1:
            with ThreadPoolExecutor(max_workers=num_tools) as executor:
                future_to_tool = {
                    executor.submit(execute_single_tool, tc): tc
                    for tc in tool_calls
                }
                for future in as_completed(future_to_tool):
                    try:
                        tool_data = future.result()
                        tool_results.append(tool_data)
                        print(f"     ✅ {tool_data['function_name']}")
                    except Exception as e:
                        print(f"     ❌ Error: {str(e)}")
        else:
            for tc in tool_calls:
                tool_data = execute_single_tool(tc)
                tool_results.append(tool_data)
                print(f"     ✅ {tool_data['function_name']}")

        return tool_results
