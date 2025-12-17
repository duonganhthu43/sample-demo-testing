"""
Simple example of using the Travel Planning Agent
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents import run_travel_planning


def main():
    # Simple trip planning
    result = run_travel_planning(
        task="Plan a 3-day trip to Tokyo",
        constraints={
            "budget": "under $1000",
            "departure_city": "Singapore",
            "travel_dates": "March 15-18"
        },
        max_iterations=10
    )

    print(f"Planning completed in {result.total_duration:.2f}s")
    print(f"Tools called: {len(result.tool_calls_made)}")

    if result.itinerary:
        print(f"Generated {len(result.itinerary.get('days', []))}-day itinerary")


if __name__ == "__main__":
    main()
