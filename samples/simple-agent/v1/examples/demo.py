"""
Naive Research Agent (v1) - Demo

This demo shows the baseline research agent in action.
It demonstrates a single agent doing everything: search, analyze, answer.

Run: python examples/demo.py
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
# Load .env from simple-agent root (parent of v1)
load_dotenv(Path(__file__).parent.parent.parent / ".env")

from src import run_research


def print_separator(title: str = ""):
    """Print a visual separator."""
    print()
    print("=" * 70)
    if title:
        print(f"  {title}")
        print("=" * 70)
    print()


def print_result(result):
    """Print research result in a formatted way."""
    print(f"Question: {result.question}")
    print("-" * 50)
    print(f"\nAnswer:\n{result.answer}")
    print(f"\n--- Stats ---")
    print(f"Thread ID: {result.thread_id}")
    print(f"Run ID: {result.run_id}")
    print(f"Iterations: {result.iterations}")
    print(f"Tool calls: {len(result.tool_calls)}")
    print(f"Duration: {result.total_duration:.2f}s")

    if result.sources:
        print(f"\nSources ({len(result.sources)}):")
        for s in result.sources[:5]:
            print(f"  - {s}")


def main():
    """Run demo."""

    print_separator("NAIVE RESEARCH AGENT (v1) - DEMO")

    print("""
This is the BASELINE version of the research agent.

Characteristics:
  - Single agent handles everything
  - Sequential tool execution (one at a time)
  - Basic prompting (no query decomposition)

Watch the agent search, analyze, and answer!
""")

    # Run research
    print_separator("Research Task")

    question = "What are AI agents and how do they work?"
    print(f"Question: {question}")
    print()

    result = run_research(
        question=question,
        max_iterations=8,
        verbose=True
    )

    print()
    print_separator("Result")
    print_result(result)

    print_separator("DEMO COMPLETE")
    print("""
What you observed:

1. AGENTIC LOOP: The agent decided when to search and when to stop
2. SEQUENTIAL: Tool calls happened one after another
3. SINGLE AGENT: One agent did everything

Next: Compare with v2, v3, v4 for improvements!
""")


if __name__ == "__main__":
    main()
