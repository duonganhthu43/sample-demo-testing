"""
Agentic Orchestrator for Travel Planning
Uses LLM function calling to autonomously plan trips
"""

import json
import time
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..utils.config import get_config
from ..utils.prompts import ORCHESTRATOR_SYSTEM_PROMPT
from .tools import TOOL_DEFINITIONS, ToolExecutor


@dataclass
class TravelPlanResult:
    """Result from travel planning"""
    task: str
    destination: str
    travel_dates: str
    total_duration: float
    iterations: int
    tool_calls_made: List[Dict[str, Any]]
    final_context: Dict[str, Any]
    itinerary: Optional[Dict[str, Any]] = None
    summary: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task": self.task,
            "destination": self.destination,
            "travel_dates": self.travel_dates,
            "total_duration": self.total_duration,
            "iterations": self.iterations,
            "tool_calls_made": self.tool_calls_made,
            "final_context": self.final_context,
            "itinerary": self.itinerary,
            "summary": self.summary
        }


class TravelPlanningOrchestrator:
    """
    Agentic orchestrator that uses LLM function calling
    to autonomously plan travel itineraries
    """

    def __init__(self, config=None):
        self.config = config or get_config()
        self.tool_executor = ToolExecutor(self.config)
        self.tool_calls_made = []

    def plan_trip(
        self,
        task: str,
        constraints: Dict[str, Any],
        max_iterations: int = 20
    ) -> TravelPlanResult:
        """
        Plan a trip autonomously using LLM function calling

        Args:
            task: Description of the trip to plan
            constraints: Budget, dates, preferences, hard constraints
            max_iterations: Maximum number of tool-calling iterations

        Returns:
            TravelPlanResult with complete trip plan
        """
        start_time = time.time()

        # Generate unique IDs for tracing
        thread_id, run_id = self.config.generate_ids()
        print(f"Starting travel planning (thread: {thread_id})")

        # Extract key information from task and constraints
        destination = self._extract_destination(task)
        travel_dates = constraints.get("travel_dates", "")
        budget = self._extract_budget(constraints.get("budget", ""))
        num_days = self._extract_num_days(task)

        # Set initial context
        self.tool_executor.set_context("destination", destination)
        self.tool_executor.set_context("travel_dates", travel_dates)
        self.tool_executor.set_context("num_days", num_days)
        self.tool_executor.set_context("constraints", constraints)

        # Get LLM client
        llm_client = self.config.get_llm_client(label="travel_orchestrator")
        llm_params = self.config.get_llm_params()

        # Build initial prompt
        user_prompt = self._build_initial_prompt(task, constraints)

        # Initialize conversation
        messages = [
            {"role": "system", "content": ORCHESTRATOR_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ]

        # Agentic loop
        iteration = 0
        self.tool_calls_made = []

        while iteration < max_iterations:
            iteration += 1
            print(f"\n--- Iteration {iteration} ---")

            try:
                # Force tool calling on early iterations to ensure research happens
                # Switch to "auto" after we have enough data (iteration > 8)
                # or when presentation is done (final output)
                has_presentation = self.tool_executor.context.get("presentation") is not None
                current_tool_choice = "auto" if (iteration > 8 or has_presentation) else "required"
                print(f"  tool_choice: {current_tool_choice}")

                # Call LLM with tools
                response = llm_client.chat.completions.create(
                    messages=messages,
                    tools=TOOL_DEFINITIONS,
                    tool_choice=current_tool_choice,
                    **llm_params
                )

                assistant_message = response.choices[0].message

                # Check if LLM wants to call tools
                if assistant_message.tool_calls:
                    # Add assistant message to conversation
                    messages.append({
                        "role": "assistant",
                        "content": assistant_message.content or "",
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

                    # Execute tools (in parallel if enabled)
                    tool_results = self._execute_tools(assistant_message.tool_calls)

                    # Add tool results to conversation
                    for tc, result in zip(assistant_message.tool_calls, tool_results):
                        self.tool_calls_made.append({
                            "iteration": iteration,
                            "tool": tc.function.name,
                            "arguments": json.loads(tc.function.arguments),
                            "result_summary": self._summarize_result(result)
                        })

                        safe_result = self._sanitize_for_llm(result)
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "name": tc.function.name,
                            "content": json.dumps(safe_result)
                        })
                else:
                    # No tool calls - LLM is done planning
                    print("Planning complete - no more tool calls")

                    # Add final response
                    if assistant_message.content:
                        messages.append({
                            "role": "assistant",
                            "content": assistant_message.content
                        })
                    break

            except Exception as e:
                print(f"Error in iteration {iteration}: {str(e)}")
                break

        # Calculate duration
        total_duration = time.time() - start_time

        # Get final context
        final_context = self.tool_executor.get_context()

        return TravelPlanResult(
            task=task,
            destination=destination,
            travel_dates=travel_dates,
            total_duration=total_duration,
            iterations=iteration,
            tool_calls_made=self.tool_calls_made,
            final_context=final_context,
            itinerary=final_context.get("itinerary"),
            summary=None
        )

    def _execute_tools(self, tool_calls) -> List[Dict[str, Any]]:
        """
        Execute tool calls, optionally in parallel

        Args:
            tool_calls: List of tool calls from LLM

        Returns:
            List of results in same order as tool calls
        """
        if self.config.agent.enable_parallel_execution and len(tool_calls) > 1:
            return self._execute_tools_parallel(tool_calls)
        else:
            return self._execute_tools_sequential(tool_calls)

    def _execute_tools_sequential(self, tool_calls) -> List[Dict[str, Any]]:
        """Execute tools sequentially"""
        results = []
        for tc in tool_calls:
            try:
                arguments = json.loads(tc.function.arguments)
                result = self.tool_executor.execute_tool(tc.function.name, arguments)
                results.append(result)
            except Exception as e:
                results.append({"success": False, "error": str(e)})
        return results

    def _sanitize_for_llm(self, data: Any) -> Any:
        if isinstance(data, dict):
            sanitized: Dict[str, Any] = {}
            for key, value in data.items():
                if key == "image_base64":
                    if value:
                        sanitized["has_image"] = True
                    continue
                sanitized[key] = self._sanitize_for_llm(value)
            return sanitized

        if isinstance(data, list):
            if len(data) > 50:
                data = data[:50]
            return [self._sanitize_for_llm(item) for item in data]

        if isinstance(data, str):
            if len(data) > 2000:
                return data[:2000] + "..."
            return data

        return data

    def _execute_tools_parallel(self, tool_calls) -> List[Dict[str, Any]]:
        """Execute tools in parallel using ThreadPoolExecutor"""
        results = [None] * len(tool_calls)

        def execute_single(index, tc):
            try:
                arguments = json.loads(tc.function.arguments)
                return index, self.tool_executor.execute_tool(tc.function.name, arguments)
            except Exception as e:
                return index, {"success": False, "error": str(e)}

        with ThreadPoolExecutor(max_workers=len(tool_calls)) as executor:
            futures = [
                executor.submit(execute_single, i, tc)
                for i, tc in enumerate(tool_calls)
            ]

            for future in as_completed(futures):
                index, result = future.result()
                results[index] = result

        return results

    def _build_initial_prompt(self, task: str, constraints: Dict[str, Any]) -> str:
        """Build the initial user prompt"""
        prompt_parts = [
            f"## Travel Planning Request\n\n{task}\n"
        ]

        if constraints:
            prompt_parts.append("## Constraints\n")

            if "budget" in constraints:
                prompt_parts.append(f"- **Budget**: {constraints['budget']}")

            if "departure_city" in constraints:
                prompt_parts.append(f"- **Departure City**: {constraints['departure_city']}")

            if "travel_dates" in constraints:
                prompt_parts.append(f"- **Travel Dates**: {constraints['travel_dates']}")

            if "preferences" in constraints:
                prompt_parts.append("\n### Preferences (nice-to-have):")
                for pref in constraints["preferences"]:
                    prompt_parts.append(f"- {pref}")

            if "hard_constraints" in constraints:
                prompt_parts.append("\n### Hard Constraints (must be met):")
                for hc in constraints["hard_constraints"]:
                    prompt_parts.append(f"- {hc}")

        prompt_parts.append("\n\n## Instructions")
        prompt_parts.append("Please research and plan this trip using the available tools.")
        prompt_parts.append("Start by researching the destination, then find flights and accommodations,")
        prompt_parts.append("research activities, and finally generate a comprehensive itinerary.")
        prompt_parts.append("Ensure all hard constraints are met and try to satisfy preferences.")

        return "\n".join(prompt_parts)

    def _extract_destination(self, task: str) -> str:
        """Extract destination from task description"""
        task_lower = task.lower()

        # Common destinations
        destinations = ["tokyo", "paris", "london", "new york", "bali",
                       "bangkok", "singapore", "seoul", "osaka", "kyoto"]

        for dest in destinations:
            if dest in task_lower:
                return dest.title()

        # Try to find "to [destination]" pattern
        import re
        match = re.search(r'to\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', task)
        if match:
            return match.group(1)

        return "Unknown"

    def _extract_budget(self, budget_str: str) -> float:
        """Extract budget amount from string"""
        import re
        match = re.search(r'[\$]?(\d+(?:,\d{3})*(?:\.\d{2})?)', budget_str)
        if match:
            return float(match.group(1).replace(',', ''))
        return 1500.0  # Default budget

    def _extract_num_days(self, task: str) -> int:
        """Extract number of days from task"""
        import re
        match = re.search(r'(\d+)[- ]day', task.lower())
        if match:
            return int(match.group(1))
        return 5  # Default

    def _summarize_result(self, result: Dict[str, Any]) -> str:
        """Create a brief summary of a tool result"""
        if not result.get("success"):
            return f"Error: {result.get('error', 'Unknown error')}"

        inner = result.get("result", {})
        if "total_options" in inner:
            return f"Found {inner['total_options']} options"
        if "is_feasible" in inner:
            return f"Feasible: {inner['is_feasible']}"
        if "total_estimated_cost" in inner:
            return f"Total cost: ${inner['total_estimated_cost']}"
        if "days" in inner:
            return f"Generated {len(inner['days'])}-day itinerary"

        return "Completed successfully"


def run_travel_planning(
    task: str,
    constraints: Optional[Dict[str, Any]] = None,
    max_iterations: int = 20
) -> TravelPlanResult:
    """
    Convenience function to run travel planning

    Args:
        task: Description of the trip to plan
        constraints: Budget, dates, preferences, hard constraints
        max_iterations: Maximum iterations for the agentic loop

    Returns:
        TravelPlanResult with complete trip plan
    """
    config = get_config()
    orchestrator = TravelPlanningOrchestrator(config)
    return orchestrator.plan_trip(
        task=task,
        constraints=constraints or {},
        max_iterations=max_iterations
    )
