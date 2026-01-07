"""
Latency Analysis Demo

Run this to generate traces with varying latencies.
Then use Lucy to analyze: "Analyze the performance"
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

from src import run_agent


def main():
    print("=" * 60)
    print("  LATENCY ANALYSIS DEMO")
    print("=" * 60)
    print()
    print("This demo has VARYING LATENCIES:")
    print("  - web_search: ~300ms (fast)")
    print("  - quick_summary: ~200ms (fast)")
    print("  - slow_analysis: ~3000ms (BOTTLENECK)")
    print()
    print("Lucy should identify slow_analysis as the bottleneck")
    print("and show latency percentiles (p50, p95, p99).")
    print()
    print("-" * 60)

    question = "Research the latest trends in artificial intelligence and provide a thorough analysis."
    print(f"Question: {question}")
    print()

    result = run_agent(question=question, max_iterations=5, verbose=True)

    print()
    print("-" * 60)
    print("RESULT")
    print("-" * 60)
    print(f"Thread ID: {result.thread_id}")
    print(f"Total Duration: {result.total_duration:.2f}s")
    print()

    print("Operation Times:")
    for op in result.operation_times:
        is_slow = op['duration_ms'] > 2000
        label = " <-- BOTTLENECK" if is_slow else ""
        print(f"  {op['operation']}: {op['duration_ms']}ms{label}")

    print()
    print("=" * 60)
    print("  NEXT: Ask Lucy 'Analyze the performance'")
    print(f"  Thread ID: {result.thread_id}")
    print("=" * 60)


if __name__ == "__main__":
    main()
