"""
Semantic Analysis Demo - Agent with Contradictory Prompt

This agent has a BADLY WRITTEN system prompt with:
- Contradictory instructions
- Conflicting requirements
- Format confusion

The debug agent should detect these prompt quality issues.
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


# =============================================================================
# BUG: CONTRADICTORY SYSTEM PROMPT
# The instructions conflict with each other, causing confusion
# =============================================================================
SYSTEM_PROMPT = """You are a research assistant. Your task is to answer questions.

IMPORTANT INSTRUCTIONS (WARNING: these contradict each other!):

TOOL USAGE:
1. You MUST use tools to gather information. Never answer without searching first.
2. You should answer questions directly from your knowledge when possible. Don't waste time searching.

SEARCH REQUIREMENTS:
3. Always call web_search at least 3 times before providing an answer.
4. Be efficient - minimize tool calls and answer quickly.

NOTE TAKING:
5. You MUST save every important finding using save_note before answering.
6. Only save the most critical findings - don't clutter with unnecessary notes.

OUTPUT FORMAT:
7. Respond with a JSON object containing your answer in this format: {"answer": "..."}
8. Just respond naturally in plain text. Don't use any special formatting.

QUALITY:
9. Provide thorough, comprehensive research with multiple sources.
10. Keep responses brief and to the point. Users don't have time for long answers.

CITATIONS:
11. Include citations for every claim you make.
12. Don't include citations - they clutter the response.

When you're done researching, provide your final answer.
Remember: Quality over quantity. Also: More searches = better results.
Be thorough but also be quick. Always search but also answer directly."""


class SemanticAnalysisAgent:
    """Agent with contradictory prompt for semantic analysis demo."""

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
            "x-label": "demo-semantic-analysis"
        }

        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL"),
            default_headers=default_headers
        )

    def _log(self, message: str):
        if self.verbose:
            print(f"[Semantic Analysis Demo] {message}")

    def run(self, question: str) -> AgentResult:
        """Run the agent on a question."""
        start_time = time.time()
        all_tool_calls = []

        self._log(f"Starting: {question}")
        self._log(f"Thread ID: {self.thread_id}")
        self._log("WARNING: System prompt has contradictory instructions!")

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

                    self._log(f"Executing tool: {tool_name}")
                    result = execute_tool(tool_name, arguments)

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

        total_duration = time.time() - start_time
        self._log(f"Complete in {total_duration:.2f}s")

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
    agent = SemanticAnalysisAgent(**kwargs)
    return agent.run(question)
