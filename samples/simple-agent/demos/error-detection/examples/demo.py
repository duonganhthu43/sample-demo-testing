"""
Error Detection Demo

Run this to generate traces with tool name mismatch errors.
Then use Lucy to analyze: "What's wrong with this run?"
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent.parent / ".env")

from src import run_agent


def main():
    print("=" * 60)
    print("  ERROR DETECTION DEMO")
    print("=" * 60)
    print()
    print("This demo has a TOOL NAME MISMATCH bug:")
    print("  - Schema defines: search_web")
    print("  - Executor expects: web_search")
    print()
    print("Lucy should detect: 'Unknown tool: search_web' errors")
    print()
    print("-" * 60)

    question = "What is machine learning?"
    print(f"Question: {question}")
    print()

    result = run_agent(question=question, max_iterations=3, verbose=True)

    print()
    print("-" * 60)
    print("RESULT")
    print("-" * 60)
    print(f"Thread ID: {result.thread_id}")
    print(f"Iterations: {result.iterations}")
    print(f"Duration: {result.total_duration:.2f}s")
    print()

    if result.errors:
        print(f"ERRORS ({len(result.errors)}):")
        for error in result.errors:
            print(f"  - {error}")

    print()
    print("=" * 60)
    print("  NEXT: Ask Lucy 'What's wrong with this run?'")
    print(f"  Thread ID: {result.thread_id}")
    print("=" * 60)


if __name__ == "__main__":
    main()
