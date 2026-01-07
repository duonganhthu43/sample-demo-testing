"""
Simple Agent v2 - Improved Prompting Demo

This demo shows the v2 research agent with enhanced prompting.
Compare this with v1 to see how better prompts improve results.

Key improvements in v2:
- Query decomposition (breaks complex questions into sub-questions)
- Chain-of-thought reasoning (explicit thinking steps)
- Better search query formulation
- Structured synthesis process

Run: python examples/demo.py
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
# Load .env from simple-agent root (parent of v2)
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

    print_separator("SIMPLE AGENT v2 - IMPROVED PROMPTING DEMO")

    print("""
This is v2 of the research agent with IMPROVED PROMPTING.

What's different from v1:
  - Query decomposition: Breaks complex questions into sub-questions
  - Chain-of-thought: Explicit reasoning before each action
  - Better search queries: Uses keywords instead of full sentences
  - Structured synthesis: Organized approach to combining findings

Same architecture as v1 (single agent, sequential execution).
The improvement is PURELY in the prompting!

Watch the agent think more systematically!
""")

    # Run research with SAME question as v1 for comparison
    print_separator("Research Task")

    question = "What are AI agents and how do they work?"
    print(f"Question: {question}")
    print()

    result = run_research(
        question=question,
        max_iterations=10,
        verbose=True
    )

    print()
    print_separator("Result")
    print_result(result)

    print_separator("DEMO COMPLETE")
    print("""
What you should observe (vs v1):

1. DECOMPOSITION: Agent breaks down the question first
2. BETTER QUERIES: Uses keywords like "AI agents definition" not full questions
3. REASONING: Explains thinking before each search
4. SYNTHESIS: More structured final answer

Same single agent, same sequential execution - just better prompts!

Next: v3 will add sub-agent architecture for specialization!
""")


if __name__ == "__main__":
    main()
