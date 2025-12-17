"""
Simple Example - Agentic Market Research
Minimal example showing how to use the agentic market research system
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents import run_agentic_research


def main():
    """
    Simple example: Research a company using agentic orchestration
    """
    print("Agentic Market Research - Simple Example\n")

    # Run agentic market research
    # The LLM will autonomously decide which tools to use
    result = run_agentic_research(
        company_name="OpenAI",
        industry="AI/LLM",
        objectives=[
            "Understand the company's business model and products",
            "Analyze their competitive position",
            "Generate a comprehensive report"
        ],
        max_iterations=15
    )

    # Print summary
    print("\nResearch Complete!")
    print(f"Company: {result.company_name}")
    print(f"Industry: {result.industry}")
    print(f"Iterations: {result.iterations}")
    print(f"Tools Called: {len(result.tool_calls_made)}")

    # Show which tools the LLM decided to use
    print("\nTools used by LLM:")
    tool_counts = {}
    for tc in result.tool_calls_made:
        tool_name = tc["tool"]
        tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1

    for tool, count in sorted(tool_counts.items()):
        print(f"  - {tool}: {count}x")

    # Display execution time
    print(f"\nCompleted in {result.total_duration:.2f} seconds")
    print("\nCheck vLLora Dashboard at http://localhost:3000 (Debug tab)")
    print("to see all the LLM requests and tool calls!")


if __name__ == "__main__":
    main()
