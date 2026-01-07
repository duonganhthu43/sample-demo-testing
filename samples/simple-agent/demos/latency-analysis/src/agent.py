"""
Latency Analysis Demo - Agent with Performance Bottleneck

This agent has multiple operations with varying latencies.
One operation (slow_analysis) is a BOTTLENECK that takes ~3s.
The debug agent should identify this and show latency percentiles.
"""

import json
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

from openai import OpenAI

from .tools import TOOL_DEFINITIONS, execute_tool


@dataclass
class AgentResult:
    """Result from agent execution"""
    question: str
    answer: str
    iterations: int = 0
    tool_calls: list[dict] = field(default_factory=list)
    total_duration: float = 0.0
    thread_id: Optional[str] = None
    run_id: Optional[str] = None
    operation_times: list[dict] = field(default_factory=list)


SYSTEM_PROMPT = """You are a research assistant with access to tools.

Available tools:
- web_search: Fast web search
- slow_analysis: Deep analysis (takes longer but thorough)
- quick_summary: Quick text summary

For comprehensive answers:
1. First search for information using web_search
2. Then perform slow_analysis on the results for deep insights
3. Optionally use quick_summary for a final summary

Always use slow_analysis for thorough research."""


class LatencyAnalysisAgent:
    """Agent with varying latency operations for performance analysis demo."""

    def __init__(
        self,
        model: str = None,
        max_iterations: int = 10,
        verbose: bool = True,
        thread_id: Optional[str] = None,
        run_id: Optional[str] = None
    ):
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.max_iterations = max_iterations
        self.verbose = verbose

        self.thread_id = thread_id or str(uuid.uuid4())
        self.run_id = run_id or str(uuid.uuid4())

        default_headers = {
            "x-thread-id": self.thread_id,
            "x-run-id": self.run_id,
            "x-label": "demo-latency-analysis"
        }

        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL"),
            default_headers=default_headers
        )

        self.operation_times = []

    def _log(self, message: str):
        if self.verbose:
            print(f"[Latency Analysis Demo] {message}")

    def run(self, question: str) -> AgentResult:
        """Run the agent on a question."""
        start_time = time.time()
        all_tool_calls = []

        self._log(f"Starting: {question}")
        self._log(f"Thread ID: {self.thread_id}")

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question}
        ]

        final_answer = ""
        iteration = 0

        while iteration < self.max_iterations:
            iteration += 1
            self._log(f"Iteration {iteration}/{self.max_iterations}")

            llm_start = time.time()
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=TOOL_DEFINITIONS,
                    tool_choice="auto"
                )
            except Exception as e:
                self._log(f"LLM call failed: {e}")
                break

            llm_duration = time.time() - llm_start
            self.operation_times.append({
                "operation": "llm_call",
                "duration_ms": int(llm_duration * 1000)
            })

            message = response.choices[0].message

            if message.tool_calls:
                self._log(f"LLM requested {len(message.tool_calls)} tool call(s)")

                messages.append({
                    "role": "assistant",
                    "content": message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in message.tool_calls
                    ]
                })

                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        arguments = {}

                    self._log(f"Executing tool: {tool_name}")

                    tool_start = time.time()
                    result = execute_tool(tool_name, arguments)
                    tool_duration = time.time() - tool_start

                    self.operation_times.append({
                        "operation": tool_name,
                        "duration_ms": int(tool_duration * 1000)
                    })

                    self._log(f"  Took {tool_duration:.2f}s")

                    all_tool_calls.append({
                        "tool": tool_name,
                        "arguments": arguments,
                        "result": result,
                        "duration_ms": int(tool_duration * 1000)
                    })

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result) if isinstance(result, dict) else str(result)
                    })
            else:
                final_answer = message.content or ""
                self._log("Agent provided final answer")
                break

        if not final_answer and iteration >= self.max_iterations:
            final_answer = "Max iterations reached."

        total_duration = time.time() - start_time
        self._log(f"Complete in {total_duration:.2f}s")

        # Log operation times
        self._log("Operation times:")
        for op in self.operation_times:
            self._log(f"  {op['operation']}: {op['duration_ms']}ms")

        return AgentResult(
            question=question,
            answer=final_answer,
            iterations=iteration,
            tool_calls=all_tool_calls,
            total_duration=total_duration,
            thread_id=self.thread_id,
            run_id=self.run_id,
            operation_times=self.operation_times.copy()
        )


def run_agent(question: str, **kwargs) -> AgentResult:
    """Convenience function to run the agent."""
    agent = LatencyAnalysisAgent(**kwargs)
    return agent.run(question)
