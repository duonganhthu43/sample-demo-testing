"""
Hidden Issues Demo - Issues that humans miss but Lucy catches

This demo shows why automated trace analysis beats manual reading:
- Tools return "success" but content has hidden problems
- Errors buried in long responses
- Issues spread across multiple spans

Run this, then try to manually find all issues in the traces.
Then ask Lucy: "Is there anything wrong?"
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

from src import run_agent


def main():
    print("=" * 70)
    print("  HIDDEN ISSUES DEMO - Lucy vs Manual Trace Reading")
    print("=" * 70)
    print()
    print("This demo shows issues that HUMANS MISS but LUCY CATCHES:")
    print()
    print("  1. SILENT FAILURES: Tools return 'success' but results are empty")
    print("  2. BURIED ERRORS: Warnings hidden in 3000+ char responses")
    print("  3. REPEATED PATTERNS: Same issue across 5+ spans (humans lose track)")
    print("  4. DEGRADING RESPONSES: Each call gets worse (hard to notice)")
    print()
    print("CHALLENGE: After running, try to manually find all issues in traces.")
    print("           Then ask Lucy - see how fast she finds them!")
    print()
    print("-" * 70)

    question = "Research the latest developments in quantum computing and explain the key breakthroughs."
    print(f"Question: {question}")
    print()
    print("Agent will make 4-6 tool calls, each with hidden issues...")
    print()

    result = run_agent(question=question, max_iterations=8, verbose=True)

    print()
    print("-" * 70)
    print("RESULT")
    print("-" * 70)
    print(f"Thread ID: {result.thread_id}")
    print(f"Iterations: {result.iterations}")
    print(f"Tool calls: {len(result.tool_calls)}")
    print(f"Duration: {result.total_duration:.2f}s")
    print()

    print("Tool call statuses (what human sees):")
    for i, tc in enumerate(result.tool_calls, 1):
        print(f"  {i}. {tc['tool']}: {tc['result_status']}")  # All look "successful"!

    print()
    print("=" * 70)
    print("  CHALLENGE: Find the Hidden Issues")
    print("=" * 70)
    print()
    print("1. Open vLLora and find this thread:")
    print(f"   Thread ID: {result.thread_id}")
    print()
    print("2. Try to manually find ALL issues by reading traces")
    print("   (Hint: There are 5+ hidden issues)")
    print()
    print("3. Then ask Lucy: 'Is there anything wrong with this run?'")
    print()
    print("Hidden issues to find:")
    print("  [ ] Cache warning from 2019")
    print("  [ ] 'Could not find any relevant results' message")
    print("  [ ] Rate limit exceeded, serving stale cache")
    print("  [ ] Document checksum mismatch")
    print("  [ ] Low confidence score (0.45)")
    print("  [ ] Content quality issues")
    print()
    print("Can you find them all manually? Lucy can - in seconds!")
    print("=" * 70)


if __name__ == "__main__":
    main()
