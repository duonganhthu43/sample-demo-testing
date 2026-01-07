"""
Semantic Analysis Demo

Run this to generate traces with contradictory prompt instructions.
Then use Lucy to analyze: "Is there anything wrong?"
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

from src import run_agent


def main():
    print("=" * 60)
    print("  SEMANTIC ANALYSIS DEMO")
    print("=" * 60)
    print()
    print("This demo has CONTRADICTORY PROMPT INSTRUCTIONS:")
    print()
    print("  Conflict 1: 'MUST use tools' vs 'answer directly'")
    print("  Conflict 2: 'at least 3 times' vs 'minimize calls'")
    print("  Conflict 3: 'JSON object' vs 'plain text'")
    print("  Conflict 4: 'thorough research' vs 'brief answers'")
    print("  Conflict 5: 'include citations' vs 'no citations'")
    print()
    print("Lucy should detect these contradictions in the system prompt.")
    print()
    print("-" * 60)

    question = "What is quantum computing?"
    print(f"Question: {question}")
    print()

    result = run_agent(question=question, max_iterations=5, verbose=True)

    print()
    print("-" * 60)
    print("RESULT")
    print("-" * 60)
    print(f"Thread ID: {result.thread_id}")
    print(f"Iterations: {result.iterations}")
    print(f"Tool calls: {len(result.tool_calls)}")
    print(f"Duration: {result.total_duration:.2f}s")

    print()
    print("Note: LLM behavior may be inconsistent due to contradictory instructions.")
    print("The debug agent should identify these prompt quality issues.")

    print()
    print("=" * 60)
    print("  NEXT: Ask Lucy 'Is there anything wrong with this run?'")
    print(f"  Thread ID: {result.thread_id}")
    print("=" * 60)


if __name__ == "__main__":
    main()
