"""
Simple Agent v3 - Sub-Agent Architecture Demo

This demo shows the v3 research agent with specialized sub-agents.
Compare this with v1/v2 to see how specialization improves results.

Key improvements in v3:
- PlannerAgent: Creates research strategy
- SearcherAgent: Executes optimized searches
- AnalyzerAgent: Extracts insights from content
- SynthesizerAgent: Creates coherent final answer

Run: python examples/demo.py
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
# Load .env from simple-agent root (parent of v3)
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
    print(f"Total sub-agent calls: {result.iterations}")
    print(f"Tool calls: {len(result.tool_calls)}")
    print(f"Duration: {result.total_duration:.2f}s")

    # v3 specific: show sub-agent usage
    if result.sub_agent_calls:
        print(f"\nSub-agent breakdown:")
        for agent, calls in result.sub_agent_calls.items():
            print(f"  - {agent.capitalize()}: {calls} call(s)")

    if result.sources:
        print(f"\nSources ({len(result.sources)}):")
        for s in result.sources[:5]:
            print(f"  - {s}")


def main():
    """Run demo."""

    print_separator("SIMPLE AGENT v3 - SUB-AGENT ARCHITECTURE DEMO")

    print("""
This is v3 of the research agent with SUB-AGENT ARCHITECTURE.

What's different from v1/v2:
  - PlannerAgent: Decomposes question into research plan
  - SearcherAgent: Specialized for executing web searches
  - AnalyzerAgent: Extracts insights from content
  - SynthesizerAgent: Combines findings into final answer

Same sequential execution as v1/v2 (v4 will add parallelism).
The improvement is in SPECIALIZATION!

Watch the agents collaborate!
""")

    # Run research with SAME question as v1/v2 for comparison
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
What you should observe (vs v1/v2):

1. CLEAR PHASES: Plan → Search → Analyze → Synthesize
2. SPECIALIZATION: Each agent focuses on its expertise
3. STRUCTURED WORKFLOW: Organized approach to research
4. BETTER HANDOFFS: Information flows between agents

Same tools, same sequential execution - just specialized agents!

Next: v4 will add parallel execution for performance!
""")


if __name__ == "__main__":
    main()
