"""
Agentic Orchestrator Demo
Demonstrates autonomous market research using LLM function calling

Usage:
    python demo.py                           # Interactive mode with default config
    python demo.py config.json               # Load parameters from JSON file
    python demo.py '{"company_name": "..."}'  # Pass JSON directly as argument
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents import run_agentic_research
from src.utils import get_config


def load_research_config(config_input: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Load research configuration from JSON file or string.

    Args:
        config_input: Path to JSON file or JSON string

    Returns:
        Dictionary with research parameters or None
    """
    if not config_input:
        return None

    # Try to load as file first
    config_path = Path(config_input)
    if config_path.exists() and config_path.is_file():
        print(f"Loading config from file: {config_path}")
        with open(config_path, 'r') as f:
            return json.load(f)

    # Try to parse as JSON string
    try:
        return json.loads(config_input)
    except json.JSONDecodeError:
        print(f"Error: '{config_input}' is not a valid JSON file or JSON string")
        sys.exit(1)


def main():
    """
    Main demo function for agentic orchestrator
    """
    print("=" * 80)
    print(" " * 15 + "AGENTIC ORCHESTRATOR DEMO")
    print(" " * 15 + "LLM-Driven Function Calling")
    print(" " * 20 + "Powered by vLLora")
    print("=" * 80)
    print()

    # Get configuration
    config = get_config()

    # Validate configuration
    print("Validating configuration...")
    if not config.validate():
        print("\n⚠️  Configuration incomplete. Please check your .env file.")
        return

    print("✓ Configuration valid\n")

    # Display configuration
    print(f"LLM Gateway: {config.llm.base_url}")
    print(f"LLM Model: {config.llm.openai_model}")
    print(f"Search Provider: {config.search.provider}")
    print()
    print("vLLora Observability: http://localhost:3000 (Debug tab)")
    print()

    # Demo: Agentic Market Research
    print("=" * 80)
    print("AGENTIC MARKET RESEARCH DEMO")
    print("=" * 80)
    print()

    # Load research config from command line argument (JSON file or string)
    research_config = load_research_config(sys.argv[1] if len(sys.argv) > 1 else None)

    if research_config:
        # Use config from JSON
        company_name = research_config.get("company_name")
        if not company_name:
            print("Error: 'company_name' is required in JSON config")
            sys.exit(1)

        industry = research_config.get("industry")
        objectives = research_config.get("objectives", [])
        additional_instructions = research_config.get("additional_instructions")
        max_iterations = research_config.get("max_iterations", 20)

        print("📄 Loaded research parameters from JSON config")
        print()
    else:
        # Default demo parameters
        company_name = "MindCare AI"
        industry = "Digital Mental Health"
        objectives = [
            "Evaluate go/no-go for launching a B2C AI mental health coaching app in Southeast Asia in 2025",
            "Estimate TAM/SAM/SOM for Vietnam, Indonesia, Philippines, and Singapore only",
            "Analyze regulatory, data privacy, and medical compliance risks by country",
            "Identify regional competitors and distribution channels",
            "Provide a risk-adjusted launch strategy and final recommendation"
        ]
        additional_instructions = None
        max_iterations = 20

    print(f"Target: {company_name}")
    print(f"Industry: {industry}")
    print(f"Mode: Autonomous (LLM decides which tools to use)")
    print()
    print("Research Objectives:")
    for i, obj in enumerate(objectives, 1):
        print(f"  {i}. {obj}")
    print()

    if additional_instructions:
        print("Additional Instructions:")
        print(f"  {additional_instructions}")
        print()

    print("⚙️  How it works:")
    print("  1. LLM receives the research request and available tools")
    print("  2. LLM autonomously decides which tools to call and in what order")
    print("  3. Each tool result is fed back to the LLM")
    print("  4. LLM continues until research is complete")
    print("  5. LLM generates final report")
    print()
    print("Available Tools:")
    print("  - research_company, research_market, research_competitors")
    print("  - perform_swot_analysis, perform_competitive_analysis, perform_trend_analysis")
    print("  - analyze_financials, analyze_technology, analyze_market_size")
    print("  - analyze_sentiment, analyze_regulatory")
    print("  - generate_report")
    print()

    input("Press Enter to start autonomous research...")
    print()

    try:
        # Run agentic market research
        result = run_agentic_research(
            company_name=company_name,
            industry=industry,
            objectives=objectives,
            additional_instructions=additional_instructions,
            max_iterations=max_iterations
        )

        print("\n" + "=" * 80)
        print("AGENTIC RESEARCH RESULTS")
        print("=" * 80)
        print()

        # Display execution summary
        print(f"Execution Summary:")
        print(f"  Total Duration: {result.total_duration:.2f}s")
        print(f"  Iterations: {result.iterations}")
        print(f"  Tools Called: {len(result.tool_calls_made)}")
        print()

        # Display tool usage
        if result.tool_calls_made:
            print(f"Tool Usage Details:")
            tool_counts = {}
            for tc in result.tool_calls_made:
                tool_name = tc["tool"]
                tool_counts[tool_name] = tool_counts.get(tool_name, 0) + 1

            for tool, count in sorted(tool_counts.items()):
                print(f"  - {tool}: {count} call(s)")
            print()

        # Display context summary
        context = result.final_context
        print(f"Research Artifacts Collected:")
        print(f"  - Research Results: {len(context.get('research', []))}")
        print(f"  - Analysis Results: {len(context.get('analysis', []))}")
        print(f"  - Specialized Results: {len(context.get('specialized', []))}")
        print()

    except Exception as e:
        print(f"\n❌ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return

    print("\n" + "=" * 80)
    print("AGENTIC DEMO COMPLETE")
    print("=" * 80)
    print()
    print("✅ Check vLLora Dashboard: http://localhost:3000")
    print("   Go to Debug tab to see all LLM requests:")
    print()
    print("   You'll see:")
    print("   - agentic_orchestrator making decisions (x-label: agentic_orchestrator)")
    print("   - research_agent gathering information (x-label: research_agent)")
    print("   - analysis_agent performing analysis (x-label: analysis_agent)")
    print("   - specialized agents for deep dives (financial_agent, technology_agent, etc.)")
    print("   - report_agent generating final report (x-label: report_agent)")
    print()
    print("🎯 Key Innovation:")
    print("   The LLM autonomously decided:")
    print("   - Which tools to call")
    print("   - In what order")
    print("   - When to stop")
    print("   - How to synthesize findings")
    print()
    print("   This is true agentic behavior - the system orchestrates itself!")
    print()


if __name__ == "__main__":
    main()
