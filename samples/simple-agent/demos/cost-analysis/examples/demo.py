"""
Cost Analysis Demo

Run this to generate traces with multi-model cost patterns.
Then use Lucy to analyze: "Why is this so expensive?"
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

from src import run_agent


def main():
    print("=" * 60)
    print("  COST ANALYSIS DEMO")
    print("=" * 60)
    print()
    print("This demo uses MULTIPLE MODELS:")
    print("  - GPT-4 for analysis (EXPENSIVE)")
    print("  - GPT-4o-mini for search (cheap)")
    print()
    print("Lucy should identify GPT-4 as the cost culprit")
    print("and recommend switching to GPT-4o-mini.")
    print()
    print("-" * 60)

    question = "What are the benefits of renewable energy?"
    print(f"Question: {question}")
    print()

    result = run_agent(
        question=question,
        expensive_model="gpt-4",
        cheap_model="gpt-4o-mini",
        verbose=True
    )

    print()
    print("-" * 60)
    print("RESULT")
    print("-" * 60)
    print(f"Thread ID: {result.thread_id}")
    print(f"Duration: {result.total_duration:.2f}s")
    print()
    print(f"Models used ({len(result.models_used)}):")
    for model in result.models_used:
        cost_label = "EXPENSIVE" if "gpt-4" == model else "cheap"
        print(f"  - {model} ({cost_label})")

    print()
    print("=" * 60)
    print("  NEXT: Ask Lucy 'Why is this so expensive?'")
    print(f"  Thread ID: {result.thread_id}")
    print("=" * 60)


if __name__ == "__main__":
    main()
