"""
Simple Agent v5 - Semantic Errors Demo

THIS VERSION HAS INTENTIONAL BUGS FOR TESTING DEBUG TRACING.

Run this demo and then use your debug tracing agent to analyze
the LLM request traces. The bugs should be detectable from:

1. Tool name mismatch: Trace shows LLM calling "search_web" but
   executor returning "Unknown tool" error

2. Conflicting prompts: Trace shows system prompt with contradictory
   instructions that may cause erratic behavior

3. Missing parameters: Trace shows LLM never sends num_results
   because it's not in the schema

4. Response format: Trace shows prompt asking for JSON but no
   response_format specified in API call

5. Error handling: Trace shows errors being logged but agent
   continuing without informing LLM

Run: python examples/demo.py
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
# Load .env from simple-agent root (parent of v5)
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

    # v5 specific: show errors encountered
    if result.errors:
        print(f"\n--- ERRORS DETECTED ({len(result.errors)}) ---")
        for i, error in enumerate(result.errors, 1):
            print(f"  {i}. {error}")
    else:
        print(f"\n--- No errors detected (bugs may be silent!) ---")

    if result.sources:
        print(f"\nSources ({len(result.sources)}):")
        for s in result.sources[:5]:
            print(f"  - {s}")


def main():
    """Run demo."""

    print_separator("SIMPLE AGENT v5 - SEMANTIC ERRORS DEMO")

    print("""
    !!! WARNING: THIS VERSION HAS INTENTIONAL BUGS !!!

This is v5 - designed for testing debug tracing agents.

BUGS TO DETECT FROM TRACES:

1. TOOL NAME MISMATCH
   - Schema defines: "search_web"
   - Executor expects: "web_search"
   - Trace shows: "Unknown tool: search_web" errors

2. CONFLICTING SYSTEM PROMPT
   - Instructions contradict each other
   - Trace shows: Confusing system message

3. MISSING PARAMETER IN SCHEMA
   - Function uses: num_results parameter
   - Schema missing: num_results not defined
   - Trace shows: LLM never sends this parameter

4. RESPONSE FORMAT MISMATCH
   - Prompt asks for: JSON output
   - API call missing: response_format parameter
   - Trace shows: Inconsistent response formats

5. POOR ERROR HANDLING
   - Errors logged but: Agent continues anyway
   - Trace shows: Errors followed by continued execution

Use your debug tracing agent to analyze the traces and identify these issues!
""")

    print_separator("Starting Buggy Research")

    question = "What are AI agents and how do they work?"
    print(f"Question: {question}")
    print()
    print("Watch for errors in the output below...")
    print()

    result = run_research(
        question=question,
        max_iterations=10,
        verbose=True
    )

    print()
    print_separator("Result")
    print_result(result)

    print_separator("DEBUG TRACING GUIDE")
    print("""
To test your debug tracing agent:

1. Check the traces in vLLora (http://localhost:3000)
   - Filter by label: "research-agent-v5-buggy"
   - Look at thread_id: """ + result.thread_id + """

2. What your debug agent should find:

   a) TOOL CALL ERRORS:
      - LLM calls "search_web"
      - Tool executor returns {"error": "Unknown tool: search_web"}
      - This happens because tools.py defines "search_web" in schema
        but execute_tool() only has "web_search" registered

   b) SYSTEM PROMPT ISSUES:
      - Contradictory instructions in system message
      - "MUST use tools" vs "answer directly from knowledge"
      - "at least 3 times" vs "minimize tool calls"

   c) SCHEMA MISMATCH:
      - web_search function accepts num_results parameter
      - Tool schema doesn't include num_results
      - LLM can't send this parameter

   d) RESPONSE FORMAT:
      - System prompt asks for JSON
      - API call doesn't set response_format
      - May cause parsing issues

3. Expected behavior after fixing:
   - Change "search_web" to "web_search" in TOOL_DEFINITIONS
   - Add num_results to schema
   - Remove contradictory prompt instructions
   - Add response_format if JSON needed
""")

    print_separator("DEMO COMPLETE")


if __name__ == "__main__":
    main()
