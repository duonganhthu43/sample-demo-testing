"""
Hidden Issues Demo - Agent that completes successfully but has hidden problems

This agent will:
1. Make multiple tool calls
2. Each returns "success" but with hidden issues
3. Agent provides a final answer (appears to work)
4. But traces contain buried errors that humans would miss
"""

import json
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

from openai import OpenAI

from .tools import TOOL_DEFINITIONS, execute_tool, reset_call_counts


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


SYSTEM_PROMPT = """You are a thorough research assistant. Your task is to research questions comprehensively.

To provide high-quality answers:
1. Use web_search multiple times with different queries to gather diverse information
2. Use fetch_document to get detailed content from relevant URLs
3. Use analyze_content to extract key insights
4. Synthesize all findings into a comprehensive answer

Be thorough - make at least 4-5 tool calls to ensure comprehensive coverage.
Always provide an answer based on what you find, even if results are limited."""


class HiddenIssuesAgent:
    """
    Agent that completes successfully but has hidden issues in traces.

    Designed to demonstrate Lucy's value:
    - Human reading traces would see "success" everywhere
    - Lucy detects semantic errors buried in responses
    """

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
            "x-label": "demo-hidden-issues"
        }

        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL"),
            default_headers=default_headers
        )

    def _log(self, message: str):
        if self.verbose:
            print(f"[Hidden Issues Demo] {message}")

    def run(self, question: str) -> AgentResult:
        """Run the agent on a question."""
        start_time = time.time()
        all_tool_calls = []

        # Reset tool call counters for fresh simulation
        reset_call_counts()

        self._log(f"Starting: {question}")
        self._log(f"Thread ID: {self.thread_id}")
        self._log("Note: Tools will return 'success' but with hidden issues")

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

                    self._log(f"Executing: {tool_name}")
                    result = execute_tool(tool_name, arguments)

                    # Log that it "succeeded" (hiding the real issues)
                    status = result.get("status", "unknown") if isinstance(result, dict) else "completed"
                    self._log(f"  Status: {status}")  # Human sees "success"

                    all_tool_calls.append({
                        "tool": tool_name,
                        "arguments": arguments,
                        "result_status": status  # Don't show full result
                    })

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result) if isinstance(result, dict) else str(result)
                    })
            else:
                final_answer = message.content or ""
                self._log("Agent provided final answer")
                self._log("(Agent completed 'successfully' - but check traces for hidden issues!)")
                break

        if not final_answer and iteration >= self.max_iterations:
            final_answer = "Research complete. Based on available information..."

        total_duration = time.time() - start_time
        self._log(f"Complete in {total_duration:.2f}s")
        self._log(f"Tool calls: {len(all_tool_calls)}")

        return AgentResult(
            question=question,
            answer=final_answer,
            iterations=iteration,
            tool_calls=all_tool_calls,
            total_duration=total_duration,
            thread_id=self.thread_id,
            run_id=self.run_id
        )


def run_agent(question: str, **kwargs) -> AgentResult:
    """Convenience function to run the agent."""
    agent = HiddenIssuesAgent(**kwargs)
    return agent.run(question)
