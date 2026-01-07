"""
Cost Analysis Demo - Multi-Model Agent

This agent uses MULTIPLE MODELS to demonstrate cost analysis:
- GPT-4 for "deep analysis" (expensive - overkill for most tasks)
- GPT-4o-mini for search operations (cheap - appropriate)

The debug agent should identify that GPT-4 is the cost culprit
and recommend switching to GPT-4o-mini.
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
    models_used: list[str] = field(default_factory=list)


SEARCH_SYSTEM_PROMPT = """You are a search assistant.
Use the web_search tool to find information.
Return the search results to the user."""

ANALYSIS_SYSTEM_PROMPT = """You are an expert analyst.
Analyze the provided information and give a comprehensive, detailed answer.
Include multiple perspectives, implications, and recommendations.
Be thorough and provide extensive analysis."""


class CostAnalysisAgent:
    """
    Multi-model agent for cost analysis demo.

    Uses GPT-4 for analysis (expensive) and GPT-4o-mini for search (cheap).
    The debug agent should identify cost optimization opportunities.
    """

    def __init__(
        self,
        expensive_model: str = "gpt-4",
        cheap_model: str = "gpt-4o-mini",
        max_iterations: int = 5,
        verbose: bool = True,
        thread_id: Optional[str] = None,
        run_id: Optional[str] = None
    ):
        self.expensive_model = expensive_model
        self.cheap_model = cheap_model
        self.max_iterations = max_iterations
        self.verbose = verbose

        self.thread_id = thread_id or str(uuid.uuid4())
        self.run_id = run_id or str(uuid.uuid4())

        default_headers = {
            "x-thread-id": self.thread_id,
            "x-run-id": self.run_id,
            "x-label": "demo-cost-analysis"
        }

        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL"),
            default_headers=default_headers
        )

        self.models_used = []

    def _log(self, message: str):
        if self.verbose:
            print(f"[Cost Analysis Demo] {message}")

    def _search_step(self, query: str) -> list[dict]:
        """Use cheap model for search (appropriate use of resources)."""
        self._log(f"Search step using {self.cheap_model} (cheap)")
        self.models_used.append(self.cheap_model)

        messages = [
            {"role": "system", "content": SEARCH_SYSTEM_PROMPT},
            {"role": "user", "content": f"Search for: {query}"}
        ]

        results = []
        iteration = 0

        while iteration < 3:  # Max 3 search iterations
            iteration += 1

            response = self.client.chat.completions.create(
                model=self.cheap_model,
                messages=messages,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto"
            )

            message = response.choices[0].message

            if message.tool_calls:
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
                    arguments = json.loads(tool_call.function.arguments)

                    self._log(f"  Searching: {arguments.get('query', '')}")
                    result = execute_tool(tool_name, arguments)
                    results.append(result)

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result)
                    })
            else:
                break

        return results

    def _analysis_step(self, question: str, search_results: list[dict]) -> str:
        """
        Use EXPENSIVE model for analysis.

        This is intentionally wasteful - GPT-4o-mini could do this just fine,
        but we use GPT-4 to demonstrate cost analysis.
        """
        self._log(f"Analysis step using {self.expensive_model} (EXPENSIVE!)")
        self.models_used.append(self.expensive_model)

        # Compile search results
        context = ""
        for result in search_results:
            if "results" in result:
                for r in result["results"]:
                    context += f"- {r.get('title', 'No title')}: {r.get('content', '')}\n"

        messages = [
            {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
            {"role": "user", "content": f"""Question: {question}

Search Results:
{context}

Provide a comprehensive analysis."""}
        ]

        # Make MULTIPLE expensive calls to really show the cost impact
        for i in range(2):  # Two expensive analysis calls
            self._log(f"  GPT-4 analysis call {i+1}/2")
            self.models_used.append(self.expensive_model)

            response = self.client.chat.completions.create(
                model=self.expensive_model,
                messages=messages
            )

            if i == 0:
                # First call: initial analysis
                messages.append({"role": "assistant", "content": response.choices[0].message.content})
                messages.append({"role": "user", "content": "Now provide additional insights and recommendations."})
            else:
                # Second call: final answer
                return response.choices[0].message.content

        return "Analysis complete."

    def run(self, question: str) -> AgentResult:
        """Run the multi-model agent."""
        start_time = time.time()

        self._log(f"Starting: {question}")
        self._log(f"Thread ID: {self.thread_id}")
        self._log(f"Using expensive model: {self.expensive_model}")
        self._log(f"Using cheap model: {self.cheap_model}")

        # Step 1: Search with cheap model
        search_results = self._search_step(question)

        # Step 2: Analyze with expensive model (wasteful!)
        final_answer = self._analysis_step(question, search_results)

        total_duration = time.time() - start_time
        self._log(f"Complete in {total_duration:.2f}s")
        self._log(f"Models used: {self.models_used}")

        return AgentResult(
            question=question,
            answer=final_answer,
            iterations=len(self.models_used),
            tool_calls=[],
            total_duration=total_duration,
            thread_id=self.thread_id,
            run_id=self.run_id,
            models_used=self.models_used.copy()
        )


def run_agent(question: str, **kwargs) -> AgentResult:
    """Convenience function to run the agent."""
    agent = CostAnalysisAgent(**kwargs)
    return agent.run(question)
