"""
Error Detection Demo - Agent with Tool Name Mismatch

This agent demonstrates a common bug: tool schema defines one name,
but the executor expects a different name. The debug agent should
detect "Unknown tool" errors in the traces.
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
    errors: list[str] = field(default_factory=list)


SYSTEM_PROMPT = """You are a helpful research assistant.

When asked a question:
1. Use the search_web tool to find information
2. Provide a comprehensive answer based on search results

Always search before answering."""


class ErrorDetectionAgent:
    """Agent with tool name mismatch bug for error detection demo."""

    def __init__(
        self,
        model: str = None,
        max_iterations: int = 5,
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
            "x-label": "demo-error-detection"
        }

        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL"),
            default_headers=default_headers
        )

        self.errors_encountered = []

    def _log(self, message: str):
        if self.verbose:
            print(f"[Error Detection Demo] {message}")

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

            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=TOOL_DEFINITIONS,
                    tool_choice="auto"
                )
            except Exception as e:
                self._log(f"LLM call failed: {e}")
                self.errors_encountered.append(f"LLM call failed: {e}")
                break

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

                    # BUG: LLM calls "search_web" but executor expects "web_search"
                    result = execute_tool(tool_name, arguments)

                    if isinstance(result, dict) and "error" in result:
                        self._log(f"Tool error: {result['error']}")
                        self.errors_encountered.append(f"Tool '{tool_name}': {result['error']}")

                    all_tool_calls.append({
                        "tool": tool_name,
                        "arguments": arguments,
                        "result": result
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
            self.errors_encountered.append("Hit max iterations")

        total_duration = time.time() - start_time
        self._log(f"Complete in {total_duration:.2f}s")

        return AgentResult(
            question=question,
            answer=final_answer,
            iterations=iteration,
            tool_calls=all_tool_calls,
            total_duration=total_duration,
            thread_id=self.thread_id,
            run_id=self.run_id,
            errors=self.errors_encountered.copy()
        )


def run_agent(question: str, **kwargs) -> AgentResult:
    """Convenience function to run the agent."""
    agent = ErrorDetectionAgent(**kwargs)
    return agent.run(question)
