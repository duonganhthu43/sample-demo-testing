"""
Travel Planning Agent Demo
Demonstrates autonomous travel planning using LLM function calling

Usage:
    python demo.py                           # Interactive mode with default config
    python demo.py travel_config.json        # Load parameters from JSON file
    python demo.py '{"task": "..."}'         # Pass JSON directly as argument
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents import run_travel_planning
from src.utils import get_config


def load_travel_config(config_input: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Load travel configuration from JSON file or string.

    Args:
        config_input: Path to JSON file or JSON string

    Returns:
        Dictionary with travel parameters or None
    """
    if not config_input:
        return None

    # Try to load as file first
    config_path = Path(config_input)
    if config_path.exists() and config_path.is_file():
        print(f"Loading config from file: {config_path}")
        with open(config_path, 'r') as f:
            return json.load(f)

    # Try to parse as JSON string
    try:
        return json.loads(config_input)
    except json.JSONDecodeError:
        print(f"Error: '{config_input}' is not a valid JSON file or JSON string")
        sys.exit(1)


def main():
    """
    Main demo function for travel planning agent
    """
    print("=" * 80)
    print(" " * 15 + "TRAVEL PLANNING AGENT DEMO")
    print(" " * 15 + "LLM-Driven Function Calling")
    print(" " * 20 + "Powered by vLLora")
    print("=" * 80)
    print()

    # Get configuration
    config = get_config()

    # Validate configuration
    print("Validating configuration...")
    if not config.validate():
        print("\nConfiguration incomplete. Please check your .env file.")
        return

    print("Configuration valid\n")

    # Display configuration
    print(f"LLM Gateway: {config.llm.base_url}")
    print(f"LLM Model: {config.llm.openai_model}")
    print()
    print("vLLora Observability: http://localhost:3000 (Debug tab)")
    print()

    # Demo: Travel Planning
    print("=" * 80)
    print("AUTONOMOUS TRAVEL PLANNING DEMO")
    print("=" * 80)
    print()

    # Load travel config from command line argument (JSON file or string)
    travel_config = load_travel_config(sys.argv[1] if len(sys.argv) > 1 else None)

    if travel_config:
        # Use config from JSON
        task = travel_config.get("task")
        if not task:
            print("Error: 'task' is required in JSON config")
            sys.exit(1)

        constraints = travel_config.get("constraints", {})
        max_iterations = travel_config.get("max_iterations", 20)

        print("Loaded travel parameters from JSON config")
        print()
    else:
        # Default demo parameters
        task = "Plan a 5-day trip to Tokyo in April"
        constraints = {
            "budget": "under $1500 total",
            "departure_city": "Singapore",
            "travel_dates": "April 10-15",
            "preferences": [
                "avoid overnight flights",
                "hotel near public transport",
                "no more than 2 activities per day"
            ],
            "hard_constraints": [
                "must arrive before 6pm local time",
                "return flight must be direct"
            ]
        }
        max_iterations = 20

    print(f"Task: {task}")
    print()
    print("Constraints:")
    if constraints.get("budget"):
        print(f"  Budget: {constraints['budget']}")
    if constraints.get("departure_city"):
        print(f"  Departure: {constraints['departure_city']}")
    if constraints.get("travel_dates"):
        print(f"  Dates: {constraints['travel_dates']}")
    print()

    if constraints.get("preferences"):
        print("Preferences:")
        for pref in constraints["preferences"]:
            print(f"  - {pref}")
        print()

    if constraints.get("hard_constraints"):
        print("Hard Constraints:")
        for hc in constraints["hard_constraints"]:
            print(f"  - {hc}")
        print()

    print("How it works:")
    print("  1. LLM receives the travel request and available tools")
    print("  2. LLM autonomously decides which tools to call")
    print("  3. Tools research flights, hotels, activities, weather, etc.")
    print("  4. LLM analyzes feasibility and optimizes the plan")
    print("  5. LLM generates comprehensive itinerary")
    print()
    print("Available Tools (13):")
    print("  Research: destination, flights, accommodations, activities")
    print("  Analysis: feasibility, cost breakdown, schedule optimization")
    print("  Specialized: budget, weather, safety, local transport")
    print("  Output: generate itinerary, generate summary")
    print()

    input("Press Enter to start autonomous planning...")
    print()

    try:
        # Run travel planning
        result = run_travel_planning(
            task=task,
            constraints=constraints,
            max_iterations=max_iterations
        )

        print("\n" + "=" * 80)
        print("TRAVEL PLANNING RESULTS")
        print("=" * 80)
        print()

        # Display execution summary
        print("Execution Summary:")
        print(f"  Total Duration: {result.total_duration:.2f}s")
        print(f"  Iterations: {result.iterations}")
        print(f"  Tools Called: {len(result.tool_calls_made)}")
        print()

        # Display tool usage
        if result.tool_calls_made:
            print("Tool Usage Details:")
            tool_counts = {}
            for tc in result.tool_calls_made:
                tool_name = tc["tool"]
                tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1

            for tool, count in sorted(tool_counts.items()):
                print(f"  - {tool}: {count} call(s)")
            print()

        # Display context summary
        context = result.final_context
        print("Planning Artifacts Collected:")
        print(f"  - Research Results: {len(context.get('research', []))}")
        print(f"  - Analysis Results: {len(context.get('analysis', []))}")
        print(f"  - Specialized Results: {len(context.get('specialized', []))}")
        print()

        # Display itinerary if generated
        if result.itinerary:
            print("Generated Itinerary:")
            print(f"  Destination: {result.itinerary.get('destination')}")
            print(f"  Days: {len(result.itinerary.get('days', []))}")
            print(f"  Estimated Cost: ${result.itinerary.get('total_estimated_cost', 'N/A')}")
            print()

    except Exception as e:
        print(f"\nDemo failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return

    print("\n" + "=" * 80)
    print("TRAVEL PLANNING DEMO COMPLETE")
    print("=" * 80)
    print()
    print("Check vLLora Dashboard: http://localhost:3000")
    print("  Go to Debug tab to see all LLM requests:")
    print()
    print("  You'll see:")
    print("  - travel_orchestrator making decisions")
    print("  - research_agent gathering flight/hotel/activity info")
    print("  - analysis_agent evaluating feasibility and costs")
    print("  - specialized agents for weather, safety, transport")
    print("  - itinerary_agent generating final plan")
    print()
    print("Key Innovation:")
    print("  The LLM autonomously decided:")
    print("  - Which tools to call")
    print("  - In what order")
    print("  - When to stop")
    print("  - How to synthesize everything into an itinerary")
    print()
    print("  This is true agentic behavior - the system plans itself!")
    print()


if __name__ == "__main__":
    main()
