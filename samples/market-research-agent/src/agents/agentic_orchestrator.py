"""
Agentic Orchestrator
Uses LLM function calling to autonomously decide which tools to invoke
"""

import time
import uuid
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..utils.config import get_config
from .tools import TOOL_DEFINITIONS, ToolExecutor


@dataclass
class AgenticResult:
    """Result from agentic orchestration"""
    company_name: str
    industry: str
    objectives: List[str]
    tool_calls_made: List[Dict[str, Any]] = field(default_factory=list)
    conversation_history: List[Dict[str, Any]] = field(default_factory=list)
    final_context: Dict[str, Any] = field(default_factory=dict)
    iterations: int = 0
    total_duration: float = 0.0
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "company_name": self.company_name,
            "industry": self.industry,
            "objectives": self.objectives,
            "tool_calls_made": self.tool_calls_made,
            "conversation_history": self.conversation_history,
            "final_context": self.final_context,
            "iterations": self.iterations,
            "total_duration": self.total_duration,
            "timestamp": self.timestamp
        }


class AgenticOrchestrator:
    """
    Orchestrator that uses LLM function calling to autonomously conduct research
    The LLM decides which tools to invoke based on the user's objectives
    """

    def __init__(self, config: Optional[Any] = None, max_iterations: int = 20):
        self.config = config or get_config()
        self.max_iterations = max_iterations

        # LLM client for orchestration decisions
        self.llm_client = None
        self.llm_params = self.config.get_llm_params()

        # Tool executor
        self.tool_executor = None

        print(f"AgenticOrchestrator initialized (max_iterations: {max_iterations})")

    def execute_research(
        self,
        company_name: str,
        industry: Optional[str] = None,
        objectives: Optional[List[str]] = None,
        additional_instructions: Optional[str] = None
    ) -> AgenticResult:
        """
        Execute autonomous market research using LLM function calling

        Args:
            company_name: Company to research
            industry: Industry context
            objectives: Research objectives
            additional_instructions: Additional instructions for the LLM

        Returns:
            AgenticResult with all findings
        """
        overall_start = time.time()

        # Generate unique IDs for tracing
        thread_id = str(uuid.uuid4())
        run_id = str(uuid.uuid4())
        self.config.thread_id = thread_id
        self.config.run_id = run_id

        # Initialize LLM client and tool executor with IDs
        self.llm_client = self.config.get_llm_client(label="agentic_orchestrator")
        self.tool_executor = ToolExecutor(self.config)

        print("=" * 80)
        print(f" Agentic Market Research: {company_name}")
        print("=" * 80)
        print(f"Thread ID: {thread_id}")
        print(f"Run ID: {run_id}")
        print(f"Industry: {industry or 'Auto-detect'}")
        print(f"Mode: LLM-driven function calling")
        print()

        # Build initial prompt
        objectives_list = objectives or [
            "Comprehensive company research",
            "Market and competitive analysis",
            "Strategic insights and recommendations"
        ]

        initial_prompt = self._build_initial_prompt(
            company_name=company_name,
            industry=industry,
            objectives=objectives_list,
            additional_instructions=additional_instructions
        )

        # Initialize conversation
        messages = [
            {
                "role": "system",
                "content": self._get_system_prompt()
            },
            {
                "role": "user",
                "content": initial_prompt
            }
        ]

        # Initialize result
        result = AgenticResult(
            company_name=company_name,
            industry=industry or "General",
            objectives=objectives_list,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S")
        )

        # Agentic loop: LLM decides which tools to call
        iteration = 0
        while iteration < self.max_iterations:
            iteration += 1

            print(f"\n{'=' * 80}")
            print(f"ITERATION {iteration}/{self.max_iterations}")
            print('=' * 80)

            # Call LLM with tools
            try:
                response = self.llm_client.chat.completions.create(
                    messages=messages,
                    tools=TOOL_DEFINITIONS,
                    tool_choice="auto",
                    **self.llm_params
                )

                assistant_message = response.choices[0].message

                # Add assistant message to conversation
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

                # Check if LLM wants to call tools
                if assistant_message.tool_calls:
                    num_tools = len(assistant_message.tool_calls)
                    print(f"\n🤖 LLM requested {num_tools} tool call(s):")

                    # Show which tools will be called
                    for tc in assistant_message.tool_calls:
                        print(f"     - {tc.function.name}")

                    # Execute tool calls in parallel
                    if num_tools > 1:
                        print(f"\n⚡ Executing {num_tools} tools in parallel...")

                    # Prepare tool execution tasks
                    def execute_single_tool(tool_call):
                        """Execute a single tool call"""
                        function_name = tool_call.function.name
                        function_args = json.loads(tool_call.function.arguments)

                        # Execute tool
                        tool_result = self.tool_executor.execute_tool(
                            tool_name=function_name,
                            arguments=function_args
                        )

                        return {
                            "tool_call_id": tool_call.id,
                            "function_name": function_name,
                            "function_args": function_args,
                            "result": tool_result
                        }

                    # Execute all tool calls in parallel using ThreadPoolExecutor
                    tool_results = []
                    with ThreadPoolExecutor(max_workers=num_tools) as executor:
                        # Submit all tasks
                        future_to_tool = {
                            executor.submit(execute_single_tool, tc): tc
                            for tc in assistant_message.tool_calls
                        }

                        # Collect results as they complete
                        for future in as_completed(future_to_tool):
                            tool_call = future_to_tool[future]
                            try:
                                tool_data = future.result()
                                tool_results.append(tool_data)
                                print(f"     ✅ Completed: {tool_data['function_name']}")
                            except Exception as e:
                                print(f"     ❌ Error executing {tool_call.function.name}: {str(e)}")
                                # Still add error result
                                tool_results.append({
                                    "tool_call_id": tool_call.id,
                                    "function_name": tool_call.function.name,
                                    "function_args": json.loads(tool_call.function.arguments),
                                    "result": {"success": False, "error": str(e)}
                                })

                    # Record all tool calls and add to conversation
                    for tool_data in tool_results:
                        # Record tool call
                        result.tool_calls_made.append({
                            "iteration": iteration,
                            "tool": tool_data["function_name"],
                            "arguments": tool_data["function_args"],
                            "result": tool_data["result"]
                        })

                        # Add tool result to conversation
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_data["tool_call_id"],
                            "name": tool_data["function_name"],
                            "content": json.dumps(tool_data["result"])
                        })

                else:
                    # No more tool calls - LLM is done
                    print(f"\n✅ LLM has completed the research")
                    if assistant_message.content:
                        print(f"\nFinal summary from LLM:")
                        print("-" * 80)
                        print(assistant_message.content)
                    break

            except Exception as e:
                print(f"\n❌ Error in iteration {iteration}: {str(e)}")
                import traceback
                traceback.print_exc()
                break

        # Store final results
        result.iterations = iteration
        result.conversation_history = messages
        result.final_context = self.tool_executor.get_context()
        result.total_duration = time.time() - overall_start

        print(f"\n{'=' * 80}")
        print("AGENTIC RESEARCH COMPLETE")
        print('=' * 80)
        print(f"Total Duration: {result.total_duration:.2f}s")
        print(f"Iterations: {result.iterations}")
        print(f"Tools Called: {len(result.tool_calls_made)}")
        print()

        # Print tool call summary
        if result.tool_calls_made:
            print("Tool Calls Summary:")
            tool_counts = {}
            for tc in result.tool_calls_made:
                tool_name = tc["tool"]
                tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1

            for tool, count in sorted(tool_counts.items()):
                print(f"  - {tool}: {count} call(s)")

        print()

        return result

    def _get_system_prompt(self) -> str:
        """Get system prompt for agentic orchestrator"""
        return """You are an expert market research orchestrator with access to specialized research tools.

Your role is to autonomously conduct comprehensive market research by strategically using the available tools via function calling.

STRATEGIC APPROACH:
1. Start with foundational research (company, market, competitors)
2. Perform core analysis (SWOT, competitive, trends) based on research findings
3. Use specialized tools for deep-dive analysis when objectives require it
4. Invoke quality review if high-quality output is critical
5. Generate comprehensive report as the final deliverable
6. When research is complete, provide a brief executive summary

DECISION-MAKING GUIDELINES:
- Be strategic and efficient - only call tools that serve the research objectives
- Build context progressively - later tool calls benefit from earlier results
- Each tool call should add meaningful value
- Avoid redundant or unnecessary analysis
- Always call generate_report as the final step to create the deliverable
- When finished with all research and report generation, provide a concise summary of key findings
- Tailor your approach based on the specific research objectives provided

Remember: The available tools and their descriptions are provided via function calling. Choose wisely based on the research objectives.
"""

    def _build_initial_prompt(
        self,
        company_name: str,
        industry: Optional[str],
        objectives: List[str],
        additional_instructions: Optional[str]
    ) -> str:
        """Build initial user prompt"""
        prompt = f"""Conduct comprehensive market research for:

Company: {company_name}
Industry: {industry or "Please identify"}

Research Objectives:
"""
        for i, obj in enumerate(objectives, 1):
            prompt += f"{i}. {obj}\n"

        if additional_instructions:
            prompt += f"\nAdditional Instructions:\n{additional_instructions}\n"

        prompt += """
Please use the available tools to gather information and achieve these objectives.
Be thorough but efficient - use your judgment to determine which tools are most relevant.
When you have completed the research, call generate_report to create the final deliverable.
"""

        return prompt


# Convenience function
def run_agentic_research(
    company_name: str,
    industry: Optional[str] = None,
    objectives: Optional[List[str]] = None,
    additional_instructions: Optional[str] = None,
    max_iterations: int = 20
) -> AgenticResult:
    """
    Run autonomous market research using LLM function calling

    Args:
        company_name: Company to research
        industry: Industry context
        objectives: Research objectives
        additional_instructions: Additional instructions
        max_iterations: Maximum tool-calling iterations

    Returns:
        AgenticResult with all findings
    """
    config = get_config()
    orchestrator = AgenticOrchestrator(config, max_iterations=max_iterations)

    return orchestrator.execute_research(
        company_name=company_name,
        industry=industry,
        objectives=objectives,
        additional_instructions=additional_instructions
    )
