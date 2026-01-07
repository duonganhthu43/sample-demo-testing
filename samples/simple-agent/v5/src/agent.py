"""
Simple Agent v5 - Semantic Errors for Debug Testing

THIS VERSION HAS INTENTIONAL BUGS FOR TESTING DEBUG TRACING AGENTS.

The bugs are designed to be detectable through LLM trace analysis:

1. TOOL NAME MISMATCH: Tool schema defines "search_web" but executor expects "web_search"
   - Trace shows: LLM calls "search_web" -> executor returns "Unknown tool" error

2. CONFLICTING SYSTEM PROMPT: Instructions contradict each other
   - Trace shows: LLM receives confusing instructions, may behave inconsistently

3. MISSING PARAMETER IN SCHEMA: num_results not in schema but used in function
   - Trace shows: LLM never sends num_results, always uses default

4. RESPONSE FORMAT MISMATCH: Asks for JSON but doesn't set response_format
   - Trace shows: LLM may not return valid JSON consistently

5. INFINITE LOOP RISK: No proper termination condition check
   - Trace shows: Agent may keep making tool calls without concluding
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
    errors: list[str] = field(default_factory=list)  # Track errors for debugging


# =============================================================================
# BUG #2: CONFLICTING SYSTEM PROMPT
# The instructions are contradictory and confusing
# =============================================================================
SYSTEM_PROMPT = """You are a research assistant. Your task is to research questions thoroughly.

IMPORTANT INSTRUCTIONS (these conflict with each other - BUG!):

1. You MUST use tools to gather information. Never answer without searching first.
2. You should answer questions directly from your knowledge when possible. Don't waste time searching.
3. Always call search_web at least 3 times before answering.
4. Be efficient - minimize tool calls and answer quickly.
5. You MUST save every finding using save_finding before providing an answer.
6. Only save the most critical findings - don't clutter with unnecessary saves.

OUTPUT FORMAT:
- Respond with a JSON object containing your answer
- Just respond naturally in plain text
- Include citations for every claim
- Keep responses brief without citations

When you're done researching, provide your final answer.
If you have nothing more to search, just answer the question.
Never answer without doing at least 5 searches first.

Remember: Quality over quantity. Also: More searches = better results."""


class ResearchAgentV5:
    """
    Research Agent v5 - Contains intentional semantic errors for debug testing.

    This agent has several bugs that should be detectable through trace analysis:
    1. Tool name mismatch (search_web vs web_search)
    2. Conflicting system prompt instructions
    3. Missing response_format for JSON requests
    4. Poor error handling that hides issues
    5. No proper loop termination logic
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

        # Generate observability IDs
        self.thread_id = thread_id or str(uuid.uuid4())
        self.run_id = run_id or str(uuid.uuid4())

        # Build headers for observability
        default_headers = {
            "x-thread-id": self.thread_id,
            "x-run-id": self.run_id,
            "x-label": "research-agent-v5-buggy"  # Label indicates this is the buggy version
        }

        # Initialize OpenAI client
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL"),
            default_headers=default_headers
        )

        self.errors_encountered = []

    def _log(self, message: str):
        if self.verbose:
            print(f"[Research Agent v5-BUGGY] {message}")

    def research(self, question: str) -> ResearchResult:
        """
        Research a question using the agentic loop.

        Contains several bugs that affect LLM behavior and should be visible in traces.
        """
        start_time = time.time()
        all_tool_calls = []
        sources = set()

        clear_findings()

        self._log(f"Starting research: {question}")
        self._log(f"Thread ID: {self.thread_id}")
        self._log(f"Run ID: {self.run_id}")
        self._log("WARNING: This version has intentional bugs for testing!")

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Research this question and provide a comprehensive answer:\n\n{question}"}
        ]

        final_answer = ""
        iteration = 0

        # BUG #5: Loop condition doesn't properly check for completion
        while iteration < self.max_iterations:
            iteration += 1
            self._log(f"Iteration {iteration}/{self.max_iterations}")

            try:
                # BUG #4: Asking for JSON in prompt but not setting response_format
                # This can cause inconsistent responses
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=TOOL_DEFINITIONS,
                    tool_choice="auto"
                    # Missing: response_format={"type": "json_object"} even though prompt asks for JSON
                )
            except Exception as e:
                self._log(f"LLM call failed: {e}")
                self.errors_encountered.append(f"LLM call failed: {e}")
                break

            message = response.choices[0].message

            # Check if we have tool calls
            if message.tool_calls:
                self._log(f"LLM requested {len(message.tool_calls)} tool call(s)")

                # Add assistant message with tool calls
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

                # Execute each tool call
                for tool_call in message.tool_calls:
                    tool_name = tool_call.function.name
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError as e:
                        self._log(f"Failed to parse arguments: {e}")
                        self.errors_encountered.append(f"JSON parse error: {e}")
                        arguments = {}

                    self._log(f"Executing tool: {tool_name}")
                    self._log(f"Arguments: {arguments}")

                    # BUG #1 manifests here: LLM calls "search_web" but executor only knows "web_search"
                    result = execute_tool(tool_name, arguments)

                    # BUG: Poor error handling - we log but continue anyway
                    if isinstance(result, dict) and "error" in result:
                        self._log(f"Tool error: {result['error']}")
                        self.errors_encountered.append(f"Tool '{tool_name}': {result['error']}")
                        # BUG: We don't inform the LLM about the error properly

                    all_tool_calls.append({
                        "tool": tool_name,
                        "arguments": arguments,
                        "result": result
                    })

                    # Track sources (BUG: might fail if result structure unexpected)
                    try:
                        if isinstance(result, dict) and "results" in result:
                            for r in result.get("results", []):
                                if r.get("url"):
                                    sources.add(r["url"])
                    except:
                        pass  # BUG: Silent failure, hides issues

                    # Add tool response
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result) if isinstance(result, dict) else str(result)
                    })
            else:
                # No tool calls - this should be the final answer
                final_answer = message.content or ""
                self._log("LLM provided final answer")
                break

        # BUG: If we hit max_iterations without an answer, we don't handle it well
        if not final_answer and iteration >= self.max_iterations:
            final_answer = "Research incomplete - maximum iterations reached."
            self.errors_encountered.append("Hit max iterations without completion")

        total_duration = time.time() - start_time
        self._log(f"Research complete in {total_duration:.2f}s")
        self._log(f"Errors encountered: {len(self.errors_encountered)}")

        return ResearchResult(
            question=question,
            answer=final_answer,
            findings=get_all_findings(),
            sources=list(sources),
            iterations=iteration,
            tool_calls=all_tool_calls,
            total_duration=total_duration,
            thread_id=self.thread_id,
            run_id=self.run_id,
            errors=self.errors_encountered.copy()
        )


def run_research(
    question: str,
    model: str = None,
    max_iterations: int = 10,
    verbose: bool = True
) -> ResearchResult:
    """
    Convenience function to run research on a question.

    Note: This version has intentional bugs for testing debug tracing.
    """
    agent = ResearchAgentV5(
        model=model,
        max_iterations=max_iterations,
        verbose=verbose
    )
    return agent.research(question)
