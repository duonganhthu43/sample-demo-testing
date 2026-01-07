"""
Naive Research Agent (v1) - Interactive Mode

Chat with the research agent interactively.
Ask questions and watch it search, analyze, and answer.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from src import NaiveResearchAgent


def main():
    """Run interactive research session."""

    print("=" * 70)
    print("  NAIVE RESEARCH AGENT (v1) - Interactive Mode")
    print("=" * 70)
    print()
    print("This is the baseline research agent (v1).")
    print("Ask any research question and watch it work!")
    print()
    print("Available tools:")
    print("  - web_search: Search the web for information")
    print("  - get_page_content: Get detailed content from a URL")
    print("  - save_finding: Save important findings")
    print()
    print("Commands:")
    print("  'quit' or 'exit' - End the session")
    print("  'verbose on/off' - Toggle debug output")
    print()
    print("=" * 70)
    print()

    # Create agent instance
    agent = NaiveResearchAgent(
        model="gpt-4o-mini",
        max_iterations=10,
        verbose=True
    )

    verbose = True

    while True:
        try:
            # Get user input
            user_input = input("\nYour question: ").strip()

            if not user_input:
                continue

            if user_input.lower() in ["quit", "exit", "q"]:
                print("\nGoodbye!")
                break

            if user_input.lower() == "verbose on":
                verbose = True
                agent.verbose = True
                print("Verbose mode ON")
                continue

            if user_input.lower() == "verbose off":
                verbose = False
                agent.verbose = False
                print("Verbose mode OFF")
                continue

            # Run research
            print()
            result = agent.research(user_input)

            # Display results
            print()
            print("=" * 70)
            print("ANSWER:")
            print("=" * 70)
            print(result.answer)
            print()
            print("-" * 70)
            print(f"Stats: {result.iterations} iterations | {len(result.tool_calls)} tool calls | {result.total_duration:.2f}s")

            if result.sources:
                print(f"Sources: {len(result.sources)} found")

            if result.findings:
                print(f"Findings saved: {len(result.findings)}")

        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
