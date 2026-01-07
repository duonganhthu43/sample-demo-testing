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
from .tools import get_tool_definitions, ToolExecutor
from ..tools.image_utils import clear_used_images


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
    thread_id: Optional[str] = None  # vLLora thread ID for tracing
    itinerary: Optional[Dict[str, Any]] = None
    summary: Optional[Dict[str, Any]] = None
    presentation: Optional[Dict[str, Any]] = None  # Final formatted markdown

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task": self.task,
            "destination": self.destination,
            "travel_dates": self.travel_dates,
            "total_duration": self.total_duration,
            "iterations": self.iterations,
            "tool_calls_made": self.tool_calls_made,
            "final_context": self.final_context,
            "thread_id": self.thread_id,
            "itinerary": self.itinerary,
            "summary": self.summary,
            "presentation": self.presentation
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

        # Clear image deduplication tracker for new session
        clear_used_images()

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
        llm_client = self.config.get_llm_client(label="travel_planner")
        llm_params = self.config.get_llm_params()

        # Build initial prompt as structured content array
        user_content = self._build_initial_prompt(task, constraints)

        # Initialize conversation with array-structured user message
        messages = [
            {"role": "system", "content": ORCHESTRATOR_SYSTEM_PROMPT},
            {"role": "user", "content": user_content}  # Array of {"type": "text", "text": ...}
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
                tools = get_tool_definitions(self.config)
                response = llm_client.chat.completions.create(
                    messages=messages,
                    tools=tools,
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
                    presentation_completed = False
                    for tc, result in zip(assistant_message.tool_calls, tool_results):
                        self.tool_calls_made.append({
                            "iteration": iteration,
                            "tool": tc.function.name,
                            "arguments": json.loads(tc.function.arguments),
                            "result_summary": self._summarize_result(result)
                        })

                        # Check if format_presentation completed - this is the FINAL output
                        if tc.function.name == "format_presentation" and result.get("success"):
                            presentation_completed = True

                        # Use concise summary for orchestrator messages
                        # Full data is stored in tool_executor.context for specialized agents
                        summary = self._summarize_for_orchestrator(tc.function.name, result)
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "name": tc.function.name,
                            "content": summary
                        })

                    # Early termination: format_presentation is the final step
                    # No need for another LLM call - the presentation IS the final output
                    if presentation_completed:
                        print("Presentation complete - skipping final LLM call (optimization)")
                        break
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
            thread_id=thread_id,
            itinerary=final_context.get("itinerary"),
            summary=None,
            presentation=final_context.get("presentation")
        )

    def _execute_tools(self, tool_calls) -> List[Dict[str, Any]]:
        """
        Execute tool calls in parallel using ThreadPoolExecutor

        Args:
            tool_calls: List of tool calls from LLM

        Returns:
            List of results in same order as tool calls
        """
        if len(tool_calls) == 1:
            # Single tool call - execute directly
            tc = tool_calls[0]
            try:
                arguments = json.loads(tc.function.arguments)
                result = self.tool_executor.execute_tool(tc.function.name, arguments)
                return [result]
            except Exception as e:
                return [{"success": False, "error": str(e)}]

        # Multiple tool calls - execute in parallel
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

    def _build_initial_prompt(self, task: str, constraints: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Build the initial user prompt as structured content array.

        Returns an array of content parts for better LLM understanding:
        - Separates task, constraints, and instructions into distinct parts
        - Uses JSON for structured constraint data
        - Enables future multimodal content (images)
        """
        content_parts = []

        # Part 1: Task description
        content_parts.append({
            "type": "text",
            "text": f"## Travel Planning Request\n\n{task}"
        })

        # Part 2: Constraints as structured JSON
        if constraints:
            constraint_data = {
                "budget": constraints.get("budget"),
                "departure_city": constraints.get("departure_city"),
                "travel_dates": constraints.get("travel_dates"),
                "preferences": constraints.get("preferences", []),
                "hard_constraints": constraints.get("hard_constraints", [])
            }
            # Remove None values
            constraint_data = {k: v for k, v in constraint_data.items() if v}

            content_parts.append({
                "type": "text",
                "text": f"## Constraints\n\n```json\n{json.dumps(constraint_data, indent=2)}\n```"
            })

        # Part 3: Instructions
        instructions = """## Instructions

Please research and plan this trip using the available tools.
Start by researching the destination, then find flights and accommodations,
research activities, and finally generate a comprehensive itinerary.
Also analyze the weather for the trip dates.
Always run budget optimization and schedule optimization before generating the itinerary.
Ensure all hard constraints are met and try to satisfy preferences."""

        content_parts.append({
            "type": "text",
            "text": instructions
        })

        return content_parts

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

    def _summarize_for_orchestrator(self, tool_name: str, result: Dict[str, Any]) -> str:
        """
        Create a concise summary of tool result for orchestrator messages.

        IMPORTANT: Full data is stored in tool_executor.context and accessed
        by specialized agents directly. The orchestrator only needs summaries
        to decide which tool to call next.

        This reduces orchestrator input tokens by ~80% without losing data.

        Args:
            tool_name: Name of the tool that was executed
            result: Full result from the tool

        Returns:
            Concise string summary for orchestrator context
        """
        if not result.get("success"):
            error = result.get("error", "Unknown error")
            return f"❌ {tool_name} failed: {error}"

        inner = result.get("result", {})

        # Tool-specific summaries
        if tool_name == "research_destination":
            return self._summarize_destination(inner)
        elif tool_name == "research_flights":
            return self._summarize_flights(inner)
        elif tool_name == "research_accommodations":
            return self._summarize_hotels(inner)
        elif tool_name == "research_activities":
            return self._summarize_activities(inner)
        elif tool_name == "analyze_itinerary_feasibility":
            return self._summarize_feasibility(inner)
        elif tool_name == "analyze_cost_breakdown":
            return self._summarize_cost(inner)
        elif tool_name == "analyze_schedule_optimization":
            return self._summarize_schedule(inner)
        elif tool_name == "optimize_budget":
            return self._summarize_budget_optimization(inner)
        elif tool_name == "analyze_weather":
            return self._summarize_weather(inner)
        elif tool_name == "analyze_safety":
            return self._summarize_safety(inner)
        elif tool_name == "analyze_local_transport":
            return self._summarize_transport(inner)
        elif tool_name == "generate_itinerary":
            return self._summarize_itinerary(inner)
        elif tool_name == "generate_summary":
            return self._summarize_trip_summary(inner)
        elif tool_name == "format_presentation":
            # IMPORTANT: Return full presentation - this is the final output!
            # The orchestrator needs the full markdown to include in its response
            return self._get_full_presentation(inner)
        else:
            # Fallback for unknown tools
            return f"✅ {tool_name} completed successfully"

    def _summarize_destination(self, data: Dict) -> str:
        """Summarize destination research"""
        dest = data.get("destination", "Unknown")
        currency = data.get("currency", "")
        visa_req = data.get("visa_requirements", "")

        parts = [f"✅ Researched {dest}"]
        if currency:
            parts.append(f"Currency: {currency}")
        if visa_req:
            # Truncate visa requirements to first 30 chars
            parts.append(f"Visa: {visa_req[:50]}")

        return " | ".join(parts)

    def _summarize_flights(self, data: Dict) -> str:
        """Summarize flight research"""
        # Handle both naming conventions
        outbound = data.get("outbound_options", []) or data.get("outbound_flights", [])
        return_flights = data.get("return_options", []) or data.get("return_flights", [])
        total = data.get("total_options", 0)

        # Get price range
        all_flights = outbound + return_flights
        if not all_flights and total == 0:
            return "✅ No flights found"

        prices = [f.get("price", 0) for f in all_flights if f.get("price")]
        direct_count = sum(1 for f in all_flights if f.get("stops", 1) == 0)

        if prices:
            min_p, max_p = min(prices), max(prices)
            return f"✅ Found {len(outbound)} outbound + {len(return_flights)} return flights (${min_p}-${max_p}), {direct_count} direct"
        elif total > 0:
            return f"✅ Found {total} flight options"
        return f"✅ Found {len(outbound)} outbound + {len(return_flights)} return flights"

    def _summarize_hotels(self, data: Dict) -> str:
        """Summarize hotel research"""
        hotels = data.get("hotels", [])
        if not hotels:
            return "✅ No hotels found"

        prices = [h.get("price_per_night", 0) for h in hotels if h.get("price_per_night")]
        ratings = [h.get("rating", 0) for h in hotels if h.get("rating")]

        parts = [f"✅ Found {len(hotels)} hotels"]
        if prices:
            parts.append(f"${min(prices)}-${max(prices)}/night")
        if ratings:
            parts.append(f"ratings {min(ratings):.1f}-{max(ratings):.1f}")

        return " | ".join(parts)

    def _summarize_activities(self, data: Dict) -> str:
        """Summarize activities research"""
        activities = data.get("activities", [])
        if not activities:
            return "✅ No activities found"

        categories = set(a.get("category", "other") for a in activities)
        return f"✅ Found {len(activities)} activities in {len(categories)} categories: {', '.join(list(categories)[:5])}"

    def _summarize_feasibility(self, data: Dict) -> str:
        """Summarize feasibility analysis"""
        feasible = data.get("is_feasible", False)
        score = data.get("feasibility_score", 0)
        issues = data.get("issues", [])

        status = "✅ Feasible" if feasible else "⚠️ Not feasible"
        parts = [f"{status} (score: {score}/100)"]
        if issues:
            parts.append(f"{len(issues)} issues to address")
        return " | ".join(parts)

    def _summarize_cost(self, data: Dict) -> str:
        """Summarize cost breakdown"""
        total = data.get("total_estimated_cost", 0)
        within_budget = data.get("within_budget", False)

        status = "✅" if within_budget else "⚠️ Over budget"
        return f"{status} Total estimated: ${total:.0f}"

    def _summarize_schedule(self, data: Dict) -> str:
        """Summarize schedule optimization"""
        days = data.get("optimized_days", [])
        improvements = data.get("improvements", [])

        return f"✅ Optimized {len(days)}-day schedule with {len(improvements)} improvements"

    def _summarize_budget_optimization(self, data: Dict) -> str:
        """Summarize budget optimization"""
        original = data.get("original_total", 0)
        optimized = data.get("optimized_total", 0)
        savings = original - optimized if original and optimized else 0

        if savings > 0:
            return f"✅ Budget optimized: ${original:.0f} → ${optimized:.0f} (save ${savings:.0f})"
        return f"✅ Budget analysis complete: ${optimized:.0f}"

    def _summarize_weather(self, data: Dict) -> str:
        """Summarize weather analysis"""
        # Handle both naming conventions
        forecast = data.get("daily_forecast", []) or data.get("forecast", [])
        summary = data.get("summary", {})
        advisory = data.get("weather_advisory", "")

        parts = [f"✅ Weather: {len(forecast)}-day forecast"]
        if summary.get("avg_high"):
            parts.append(f"avg {summary.get('avg_high')}°C")
        elif summary.get("average_temperature"):
            parts.append(f"avg {summary.get('average_temperature')}°C")
        if advisory:
            parts.append(advisory[:50])
        return " | ".join(parts)

    def _summarize_safety(self, data: Dict) -> str:
        """Summarize safety analysis"""
        rating = data.get("overall_safety_rating", "")
        tips = data.get("safety_tips", [])
        scams = data.get("scam_warnings", [])

        parts = [f"✅ Safety: {rating}" if rating else "✅ Safety analyzed"]
        if tips:
            parts.append(f"{len(tips)} tips")
        if scams:
            parts.append(f"{len(scams)} scam warnings")
        return " | ".join(parts)

    def _summarize_transport(self, data: Dict) -> str:
        """Summarize transport analysis"""
        options = data.get("transport_options", [])
        passes = data.get("recommended_passes", [])

        parts = [f"✅ Found {len(options)} transport options"]
        if passes:
            parts.append(f"{len(passes)} recommended passes")
        return " | ".join(parts)

    def _summarize_itinerary(self, data: Dict) -> str:
        """Summarize generated itinerary"""
        days = data.get("days", [])
        total_cost = data.get("estimated_total_cost", 0)

        return f"✅ Generated {len(days)}-day itinerary | Est. cost: ${total_cost:.0f}"

    def _summarize_trip_summary(self, data: Dict) -> str:
        """Summarize trip summary"""
        highlights = data.get("highlights", [])
        checklist_items = len(data.get("checklist", []))

        return f"✅ Trip summary with {len(highlights)} highlights, {checklist_items} checklist items"

    def _summarize_presentation(self, data: Dict) -> str:
        """Summarize presentation formatting"""
        has_markdown = bool(data.get("formatted_output") or data.get("markdown"))
        images_count = data.get("images_included", 0)

        parts = ["✅ Formatted presentation ready"]
        if images_count:
            parts.append(f"{images_count} images")
        return " | ".join(parts)

    def _get_full_presentation(self, data: Dict) -> str:
        """
        Return full presentation markdown - this is the FINAL OUTPUT.

        Unlike other tools where we summarize to save tokens, the presentation
        is the final deliverable and must be returned in full so the orchestrator
        can include it in its response to the user.
        """
        markdown = data.get("markdown") or data.get("formatted_output", "")

        if markdown:
            return f"✅ Presentation formatted successfully. Here is the complete travel plan:\n\n{markdown}"

        return "✅ Presentation formatted (no markdown content)"


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
