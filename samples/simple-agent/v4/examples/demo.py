"""
Simple Agent v4 - Parallel Execution Demo

This demo shows the v4 research agent with parallel execution.
Compare this with v3 to see the performance improvement.

Key improvements in v4:
- Multiple searches executed in PARALLEL
- Concurrent content extraction from URLs
- Significant speedup over sequential execution

Run: python examples/demo.py
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
# Load .env from simple-agent root (parent of v4)
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

    # v4 specific: show parallel performance
    print(f"\n--- Performance (v4) ---")
    print(f"Parallel searches: {result.parallel_searches}")
    print(f"Actual duration: {result.total_duration:.2f}s")
    print(f"Est. sequential time: {result.sequential_time_estimate:.2f}s")
    if result.sequential_time_estimate > 0:
        speedup = result.sequential_time_estimate / result.total_duration
        print(f"Estimated speedup: {speedup:.1f}x")

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

    print_separator("SIMPLE AGENT v4 - PARALLEL EXECUTION DEMO")

    print("""
This is v4 of the research agent with PARALLEL EXECUTION.

What's different from v3:
  - Multiple search queries executed CONCURRENTLY
  - Parallel content extraction from URLs
  - Significant performance improvement

Same sub-agent architecture as v3:
  - PlannerAgent, SearcherAgent, AnalyzerAgent, SynthesizerAgent

The improvement is in PARALLEL TOOL EXECUTION!

Watch the parallel searches happen!
""")

    # Run research with SAME question as v1/v2/v3 for comparison
    print_separator("Research Task")

    question = "What are AI agents and how do they work?"
    print(f"Question: {question}")
    print()

    result = run_research(
        question=question,
        max_iterations=10,
        verbose=True,
        max_workers=4  # 4 parallel workers
    )

    print()
    print_separator("Result")
    print_result(result)

    print_separator("DEMO COMPLETE")
    print("""
What you should observe (vs v3):

1. PARALLEL SEARCHES: Multiple queries run at the same time
2. CONCURRENT EXTRACTION: Content fetched from URLs in parallel
3. FASTER EXECUTION: Significant time savings
4. SAME QUALITY: Sub-agent architecture preserved

The progression is complete:
  v1: Basic agent (baseline)
  v2: Improved prompting (better quality)
  v3: Sub-agent architecture (specialization)
  v4: Parallel execution (performance)

Each version demonstrates one key improvement!
""")


if __name__ == "__main__":
    main()
