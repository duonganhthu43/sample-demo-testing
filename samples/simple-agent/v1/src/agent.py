"""
Naive Research Agent (v1)

A simple single-agent implementation for research tasks.
This is the BASELINE version - intentionally simple to show limitations
that will be addressed in later versions.

Limitations of this naive approach:
- Single agent handles everything (no specialization)
- Sequential tool execution (no parallelism)
- Basic prompting (no query decomposition or planning)
- No structured output format
- Limited error recovery

Future versions will improve:
- v2: Better prompting (query reformulation, chain-of-thought)
- v3: Sub-agent architecture (planner, searcher, analyzer, synthesizer)
- v4: Parallel execution (concurrent searches and analysis)
"""

import json
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Optional

from openai import OpenAI

from .tools import TOOL_DEFINITIONS, execute_tool, get_all_findings, clear_findings


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


class NaiveResearchAgent:
    """
    A naive (baseline) research agent.

    This agent:
    1. Takes a research question
    2. Searches the web for information
    3. Optionally extracts more content from pages
    4. Saves key findings
    5. Synthesizes an answer

    All done by a SINGLE agent with SEQUENTIAL tool calls.
    This is intentionally simple to demonstrate the baseline approach.
    """

    # Simple system prompt - intentionally basic for v1
    SYSTEM_PROMPT = """You are a research assistant. Your job is to answer questions by searching the web and analyzing information.

Available tools:
- web_search: Search the web for information
- get_page_content: Get detailed content from a URL
- save_finding: Save important facts you discover

Process:
1. Search for relevant information
2. Read page content if you need more details
3. Save key findings as you discover them
4. Provide a comprehensive answer based on your research

Be thorough but efficient. Cite your sources."""

    def __init__(
        self,
        model: str = None,
        max_iterations: int = 10,
        verbose: bool = True,
        thread_id: Optional[str] = None,
        run_id: Optional[str] = None
    ):
        """
        Initialize the research agent.

        Args:
            model: The LLM model to use (defaults to OPENAI_MODEL env var or gpt-4o-mini)
            max_iterations: Maximum agentic loop iterations
            verbose: Whether to print debug information
            thread_id: Optional thread ID for observability (auto-generated if not provided)
            run_id: Optional run ID for observability (auto-generated if not provided)
        """
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.max_iterations = max_iterations
        self.verbose = verbose

        # Generate observability IDs
        self.thread_id = thread_id or str(uuid.uuid4())
        self.run_id = run_id or str(uuid.uuid4())

        # Build headers for observability (vLLora, etc.)
        default_headers = {
            "x-thread-id": self.thread_id,
            "x-run-id": self.run_id,
            "x-label": "naive-research-agent"
        }

        # Initialize OpenAI client
        # LLM_BASE_URL is used for gateway/proxy (e.g., vLLora)
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL"),
            default_headers=default_headers
        )

    def _log(self, message: str):
        """Print debug message if verbose mode is enabled."""
        if self.verbose:
            print(f"[Research Agent] {message}")

    def research(self, question: str) -> ResearchResult:
        """
        Research a question and provide an answer.

        This implements a naive agentic loop:
        1. Send question to LLM with tools
        2. LLM calls tools sequentially
        3. Continue until LLM provides final answer

        Args:
            question: The research question to answer

        Returns:
            ResearchResult with answer, findings, and metadata
        """
        start_time = time.time()
        all_tool_calls = []
        sources = set()

        # Clear previous findings
        clear_findings()

        # Initialize conversation
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": f"Research this question and provide a comprehensive answer:\n\n{question}"}
        ]

        self._log(f"Starting research: {question[:80]}...")
        self._log(f"Thread ID: {self.thread_id}")
        self._log(f"Run ID: {self.run_id}")

        # Agentic loop
        for iteration in range(1, self.max_iterations + 1):
            self._log(f"Iteration {iteration}/{self.max_iterations}")

            # Call LLM
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto"
            )

            assistant_message = response.choices[0].message

            # Check for tool calls
            if assistant_message.tool_calls:
                # Add assistant message
                messages.append({
                    "role": "assistant",
                    "content": assistant_message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in assistant_message.tool_calls
                    ]
                })

                # Execute tools SEQUENTIALLY (naive approach)
                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)

                    self._log(f"Tool: {tool_name}({json.dumps(tool_args)[:50]}...)")

                    # Execute tool
                    tool_result = execute_tool(tool_name, tool_args)
                    result_data = json.loads(tool_result)

                    # Track sources from search results
                    if tool_name == "web_search" and result_data.get("results"):
                        for r in result_data["results"]:
                            if r.get("url"):
                                sources.add(r["url"])

                    # Record tool call
                    all_tool_calls.append({
                        "iteration": iteration,
                        "tool": tool_name,
                        "arguments": tool_args,
                        "result": result_data
                    })

                    # Add tool result
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result
                    })

            else:
                # No tool calls = done
                final_answer = assistant_message.content or ""
                self._log(f"Research completed in {iteration} iterations")

                return ResearchResult(
                    question=question,
                    answer=final_answer,
                    findings=get_all_findings(),
                    sources=list(sources),
                    iterations=iteration,
                    tool_calls=all_tool_calls,
                    total_duration=time.time() - start_time,
                    thread_id=self.thread_id,
                    run_id=self.run_id
                )

        # Max iterations reached
        self._log("Max iterations reached - providing partial answer")

        # Get whatever answer we have
        final_response = self.client.chat.completions.create(
            model=self.model,
            messages=messages + [
                {"role": "user", "content": "Please provide your best answer based on the research so far."}
            ]
        )

        return ResearchResult(
            question=question,
            answer=final_response.choices[0].message.content or "Research incomplete.",
            findings=get_all_findings(),
            sources=list(sources),
            iterations=self.max_iterations,
            tool_calls=all_tool_calls,
            total_duration=time.time() - start_time,
            thread_id=self.thread_id,
            run_id=self.run_id
        )


def run_research(
    question: str,
    model: str = "gpt-4o-mini",
    max_iterations: int = 10,
    verbose: bool = True
) -> ResearchResult:
    """
    Convenience function to run research on a question.

    Args:
        question: The research question
        model: LLM model to use
        max_iterations: Maximum iterations
        verbose: Print debug info

    Returns:
        ResearchResult with answer and metadata
    """
    agent = NaiveResearchAgent(
        model=model,
        max_iterations=max_iterations,
        verbose=verbose
    )
    return agent.research(question)


# Backwards compatibility
SimpleAgent = NaiveResearchAgent
run_agent = run_research
AgentResult = ResearchResult
