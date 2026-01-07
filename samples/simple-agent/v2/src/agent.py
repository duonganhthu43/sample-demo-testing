"""
Simple Agent v2 - Improved Prompting

This version improves on v1 with better prompting techniques:
- Query decomposition: Breaks complex questions into sub-questions
- Chain-of-thought reasoning: Explicit thinking steps before actions
- Better search query formulation: Instructions for effective queries
- Structured thinking process: Think → Plan → Execute → Synthesize

Same architecture as v1 (single agent, sequential execution).
The improvement is PURELY in the prompting.
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


class ResearchAgentV2:
    """
    Research Agent v2 with improved prompting.

    Key improvements over v1:
    1. QUERY DECOMPOSITION: Breaks complex questions into sub-questions
    2. CHAIN-OF-THOUGHT: Explicit reasoning before each action
    3. SEARCH OPTIMIZATION: Better query formulation guidelines
    4. STRUCTURED SYNTHESIS: Organized approach to combining findings

    Architecture remains the same as v1 (single agent, sequential).
    """

    # Improved system prompt with advanced prompting techniques
    SYSTEM_PROMPT = """You are an expert research assistant with exceptional analytical skills. Your task is to thoroughly research questions and provide comprehensive, well-sourced answers.

## Your Research Methodology

### Step 1: DECOMPOSE the Question
Before searching, break down complex questions into simpler sub-questions:
- What are the key concepts that need to be understood?
- What specific facts need to be gathered?
- Are there different perspectives to consider?
- What background context is needed?

### Step 2: PLAN Your Search Strategy
Think about the best search queries:
- Use specific, targeted keywords (not full sentences)
- Consider synonyms and related terms
- Plan multiple searches to cover different aspects
- Prioritize authoritative sources

### Step 3: EXECUTE Searches Systematically
For each sub-question:
1. Formulate an effective search query (3-5 keywords work best)
2. Review the results critically
3. Extract detailed content from promising sources
4. Save key findings with proper attribution

### Step 4: SYNTHESIZE Your Answer
Combine findings into a coherent response:
- Address all aspects of the original question
- Present information in a logical structure
- Cite sources for key facts
- Acknowledge any limitations or uncertainties

## Search Query Best Practices
- BAD: "What are the main applications and use cases of artificial intelligence in healthcare?"
- GOOD: "AI healthcare applications 2024"
- BAD: "How does machine learning work and what are its different types?"
- GOOD: "machine learning types algorithms"

## Available Tools
- `web_search`: Search the web for information. Use specific keywords, not questions.
- `get_page_content`: Extract detailed content from a URL for deeper analysis.
- `save_finding`: Record important facts with topic categorization and source attribution.

## Chain-of-Thought Process
Before EACH action, briefly state:
1. What information you're looking for
2. Why this search/action is relevant
3. What you expect to learn

After EACH tool result, briefly reflect:
1. What did you learn?
2. What gaps remain?
3. What should you search next?

## Quality Standards
- Be thorough: Cover multiple aspects of the question
- Be accurate: Only state facts you've verified from sources
- Be balanced: Present multiple perspectives when relevant
- Be concise: Synthesize, don't just list facts
- Be honest: Acknowledge when information is limited or uncertain"""

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
            "x-label": "research-agent-v2"  # Different label for v2
        }

        # Initialize OpenAI client
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL"),
            default_headers=default_headers
        )

    def _log(self, message: str):
        """Print debug message if verbose mode is enabled."""
        if self.verbose:
            print(f"[Research Agent v2] {message}")

    def research(self, question: str) -> ResearchResult:
        """
        Research a question using improved prompting techniques.

        The key difference from v1 is the enhanced system prompt that guides
        the LLM to:
        1. Decompose the question first
        2. Think through each step (chain-of-thought)
        3. Use optimized search queries
        4. Synthesize findings systematically

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

        # Enhanced user message that encourages decomposition
        user_message = f"""Please research the following question thoroughly:

**Question:** {question}

Before searching, take a moment to:
1. Identify the key concepts in this question
2. Break it down into 2-3 sub-questions if it's complex
3. Plan your search strategy

Then proceed with your research, thinking through each step."""

        # Initialize conversation
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_message}
        ]

        self._log(f"Starting research: {question[:80]}...")
        self._log(f"Thread ID: {self.thread_id}")
        self._log(f"Run ID: {self.run_id}")

        # Agentic loop (same structure as v1)
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

                # Execute tools SEQUENTIALLY (same as v1)
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
                {"role": "user", "content": "Please synthesize your research into a comprehensive answer based on what you've found so far."}
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
    model: str = None,
    max_iterations: int = 10,
    verbose: bool = True
) -> ResearchResult:
    """
    Convenience function to run research on a question.

    Args:
        question: The research question
        model: LLM model to use (defaults to env var)
        max_iterations: Maximum iterations
        verbose: Print debug info

    Returns:
        ResearchResult with answer and metadata
    """
    agent = ResearchAgentV2(
        model=model,
        max_iterations=max_iterations,
        verbose=verbose
    )
    return agent.research(question)
