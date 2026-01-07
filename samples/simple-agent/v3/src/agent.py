"""
Simple Agent v3 - Sub-Agent Architecture

This version introduces specialized sub-agents that work together:
- PlannerAgent: Decomposes questions into research plans
- SearcherAgent: Executes optimized web searches
- AnalyzerAgent: Extracts insights from content
- SynthesizerAgent: Combines findings into final answer

Key architectural change from v1/v2:
- Instead of one agent doing everything, we have specialized agents
- Each agent has a focused role and optimized prompt
- An orchestrator coordinates the workflow

Still uses sequential execution (v4 will add parallelism).
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
    # v3 additions
    research_plan: Optional[str] = None
    sub_agent_calls: dict = field(default_factory=dict)


# =============================================================================
# Sub-Agent Prompts
# =============================================================================

PLANNER_PROMPT = """You are a Research Planner. Your ONLY job is to analyze questions and create research plans.

Given a research question, you must:
1. Identify the key concepts that need to be understood
2. Break down complex questions into 2-4 simpler sub-questions
3. Prioritize which aspects to research first
4. Suggest specific search queries for each sub-question

OUTPUT FORMAT (respond in this exact JSON format):
{
    "main_topic": "The core topic being researched",
    "sub_questions": [
        "First sub-question to answer",
        "Second sub-question to answer"
    ],
    "search_queries": [
        "optimized search query 1",
        "optimized search query 2"
    ],
    "priority_order": "Explanation of which to research first and why"
}

IMPORTANT:
- Search queries should be 3-5 keywords, NOT full sentences
- Focus on factual, searchable terms
- Consider different angles of the topic"""

SEARCHER_PROMPT = """You are a Research Searcher. Your ONLY job is to execute web searches and find relevant information.

You will receive search queries from the Planner. For each query:
1. Execute the web_search tool
2. Review the results critically
3. Identify the most promising sources for deeper analysis
4. Use get_page_content on the best 1-2 sources

GUIDELINES:
- Focus on authoritative sources (academic, official, reputable news)
- Look for recent information when relevant
- Note conflicting information from different sources
- Save important findings using save_finding tool

After searching, summarize what you found and what sources look most valuable."""

ANALYZER_PROMPT = """You are a Research Analyzer. Your ONLY job is to analyze content and extract key insights.

You will receive content from the Searcher. For each piece of content:
1. Identify the main claims and facts
2. Evaluate source credibility
3. Extract specific data points, statistics, or quotes
4. Note any biases or limitations

OUTPUT FORMAT:
For each source analyzed, provide:
- Key facts discovered
- Relevance to the research question
- Credibility assessment
- Any caveats or limitations

Use the save_finding tool to record important insights with proper attribution."""

SYNTHESIZER_PROMPT = """You are a Research Synthesizer. Your ONLY job is to combine findings into a coherent, well-structured answer.

You will receive analyzed findings from the research process. Your task:
1. Organize information logically
2. Address all aspects of the original question
3. Present a balanced view with multiple perspectives
4. Cite sources for key claims
5. Acknowledge limitations or gaps in the research

OUTPUT REQUIREMENTS:
- Start with a clear, direct answer to the question
- Support with evidence from the research
- Use clear structure with sections if needed
- End with any caveats or areas needing more research
- Include source citations"""


class ResearchAgentV3:
    """
    Research Agent v3 with sub-agent architecture.

    Key improvements over v2:
    1. SPECIALIZATION: Each sub-agent has a focused role
    2. MODULAR DESIGN: Easy to improve individual components
    3. CLEAR WORKFLOW: Plan → Search → Analyze → Synthesize

    Architecture:
    - Orchestrator coordinates the workflow
    - PlannerAgent creates the research plan
    - SearcherAgent executes searches
    - AnalyzerAgent extracts insights
    - SynthesizerAgent creates the final answer
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
            "x-label": "research-agent-v3"
        }

        # Initialize OpenAI client (shared by all sub-agents)
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("LLM_BASE_URL"),
            default_headers=default_headers
        )

        # Track sub-agent usage
        self.sub_agent_calls = {
            "planner": 0,
            "searcher": 0,
            "analyzer": 0,
            "synthesizer": 0
        }

    def _log(self, message: str):
        if self.verbose:
            print(f"[Research Agent v3] {message}")

    def _call_sub_agent(
        self,
        agent_name: str,
        system_prompt: str,
        user_message: str,
        tools: list = None,
        execute_tools: bool = False
    ) -> tuple[str, list]:
        """
        Call a sub-agent with its specialized prompt.

        Args:
            agent_name: Name for logging
            system_prompt: The sub-agent's system prompt
            user_message: The task for this sub-agent
            tools: Tool definitions (optional)
            execute_tools: Whether to execute tool calls

        Returns:
            Tuple of (response_text, tool_call_records)
        """
        self._log(f"[{agent_name}] Starting...")
        self.sub_agent_calls[agent_name.lower()] += 1

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]

        tool_records = []

        # Simple loop for tool execution
        for _ in range(self.max_iterations):
            kwargs = {"model": self.model, "messages": messages}
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"

            response = self.client.chat.completions.create(**kwargs)
            assistant_message = response.choices[0].message

            if assistant_message.tool_calls and execute_tools:
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

                # Execute tools
                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)

                    self._log(f"[{agent_name}] Tool: {tool_name}")

                    tool_result = execute_tool(tool_name, tool_args)

                    tool_records.append({
                        "agent": agent_name,
                        "tool": tool_name,
                        "arguments": tool_args,
                        "result": json.loads(tool_result)
                    })

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": tool_result
                    })
            else:
                # No more tool calls
                self._log(f"[{agent_name}] Complete")
                return assistant_message.content or "", tool_records

        return messages[-1].get("content", ""), tool_records

    def research(self, question: str) -> ResearchResult:
        """
        Research a question using the sub-agent architecture.

        Workflow:
        1. PLANNER: Decompose question into research plan
        2. SEARCHER: Execute searches based on plan
        3. ANALYZER: Extract insights from results
        4. SYNTHESIZER: Create final answer

        Args:
            question: The research question

        Returns:
            ResearchResult with answer and metadata
        """
        start_time = time.time()
        all_tool_calls = []
        sources = set()

        clear_findings()

        self._log(f"Starting research: {question[:80]}...")
        self._log(f"Thread ID: {self.thread_id}")
        self._log(f"Run ID: {self.run_id}")

        # =================================================================
        # Step 1: PLANNER - Create research plan
        # =================================================================
        self._log("=" * 50)
        self._log("PHASE 1: PLANNING")
        self._log("=" * 50)

        plan_response, _ = self._call_sub_agent(
            "Planner",
            PLANNER_PROMPT,
            f"Create a research plan for this question:\n\n{question}"
        )

        research_plan = plan_response

        # Try to parse the plan for search queries
        search_queries = []
        try:
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{[\s\S]*\}', plan_response)
            if json_match:
                plan_data = json.loads(json_match.group())
                search_queries = plan_data.get("search_queries", [])
                self._log(f"Extracted {len(search_queries)} search queries from plan")
        except:
            # Fallback: use the question as search query
            search_queries = [question]
            self._log("Could not parse plan, using original question")

        # =================================================================
        # Step 2: SEARCHER - Execute searches
        # =================================================================
        self._log("=" * 50)
        self._log("PHASE 2: SEARCHING")
        self._log("=" * 50)

        search_context = f"""Research Plan:
{plan_response}

Execute searches for these queries:
{json.dumps(search_queries, indent=2)}

Search each query and identify valuable sources for analysis."""

        search_response, search_tools = self._call_sub_agent(
            "Searcher",
            SEARCHER_PROMPT,
            search_context,
            tools=TOOL_DEFINITIONS,
            execute_tools=True
        )

        all_tool_calls.extend(search_tools)

        # Collect sources from search results
        for tc in search_tools:
            if tc["tool"] == "web_search":
                for r in tc["result"].get("results", []):
                    if r.get("url"):
                        sources.add(r["url"])

        # =================================================================
        # Step 3: ANALYZER - Extract insights
        # =================================================================
        self._log("=" * 50)
        self._log("PHASE 3: ANALYZING")
        self._log("=" * 50)

        # Compile search results for analysis
        search_summary = f"""Original Question: {question}

Research Plan:
{plan_response}

Search Results Summary:
{search_response}

Analyze these findings and extract key insights. Use save_finding to record important facts."""

        analyze_response, analyze_tools = self._call_sub_agent(
            "Analyzer",
            ANALYZER_PROMPT,
            search_summary,
            tools=TOOL_DEFINITIONS,
            execute_tools=True
        )

        all_tool_calls.extend(analyze_tools)

        # =================================================================
        # Step 4: SYNTHESIZER - Create final answer
        # =================================================================
        self._log("=" * 50)
        self._log("PHASE 4: SYNTHESIZING")
        self._log("=" * 50)

        # Get all findings
        findings = get_all_findings()

        synthesis_context = f"""Original Question: {question}

Research Plan:
{plan_response}

Search Summary:
{search_response}

Analysis:
{analyze_response}

Saved Findings:
{json.dumps(findings, indent=2)}

Sources Used:
{json.dumps(list(sources), indent=2)}

Create a comprehensive, well-structured answer to the original question based on all the research above."""

        final_answer, _ = self._call_sub_agent(
            "Synthesizer",
            SYNTHESIZER_PROMPT,
            synthesis_context
        )

        self._log("=" * 50)
        self._log("RESEARCH COMPLETE")
        self._log("=" * 50)

        return ResearchResult(
            question=question,
            answer=final_answer,
            findings=findings,
            sources=list(sources),
            iterations=sum(self.sub_agent_calls.values()),
            tool_calls=all_tool_calls,
            total_duration=time.time() - start_time,
            thread_id=self.thread_id,
            run_id=self.run_id,
            research_plan=research_plan,
            sub_agent_calls=self.sub_agent_calls.copy()
        )


def run_research(
    question: str,
    model: str = None,
    max_iterations: int = 10,
    verbose: bool = True
) -> ResearchResult:
    """
    Convenience function to run research on a question.
    """
    agent = ResearchAgentV3(
        model=model,
        max_iterations=max_iterations,
        verbose=verbose
    )
    return agent.research(question)
