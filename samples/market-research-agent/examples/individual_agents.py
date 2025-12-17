"""
Individual Agents Example
Demonstrates using each agent independently for custom workflows
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents import ResearchAgent, AnalysisAgent, ReportAgent
from src.utils import get_config


def main():
    """
    Example of using agents individually
    """
    print("="*80)
    print("INDIVIDUAL AGENTS EXAMPLE")
    print("="*80)
    print()

    config = get_config()

    # Initialize agents
    research_agent = ResearchAgent(config)
    analysis_agent = AnalysisAgent(config)
    report_agent = ReportAgent(config)

    company_name = "GitHub"
    industry = "Developer Tools"

    # ===========================
    # 1. Research Agent
    # ===========================
    print("1. RESEARCH AGENT")
    print("-" * 80)
    print()

    print("Researching company...")
    company_research = research_agent.research_company(company_name, depth="standard")

    print(f"✓ Research complete")
    print(f"  Topic: {company_research.topic}")
    print(f"  Type: {company_research.research_type}")
    print(f"  Sources: {len(company_research.sources)}")
    print(f"  Confidence: {company_research.confidence:.2%}")
    print()

    # ===========================
    # 2. Analysis Agent
    # ===========================
    print("2. ANALYSIS AGENT")
    print("-" * 80)
    print()

    print("Performing SWOT analysis...")
    swot_analysis = analysis_agent.perform_swot_analysis(
        company_name,
        company_research.to_dict()
    )

    print(f"✓ SWOT analysis complete")
    print(f"  Subject: {swot_analysis.subject}")
    print(f"  Type: {swot_analysis.analysis_type}")
    print(f"  Recommendations: {len(swot_analysis.recommendations)}")
    print(f"  Confidence: {swot_analysis.confidence:.2%}")
    print()

    # Display SWOT matrix
    if "visualization" in swot_analysis.insights:
        print("SWOT Matrix:")
        print(swot_analysis.insights["visualization"])
        print()

    # ===========================
    # 3. Report Agent
    # ===========================
    print("3. REPORT AGENT")
    print("-" * 80)
    print()

    print("Generating executive summary...")
    exec_summary = report_agent.generate_executive_summary(
        company_name,
        industry,
        company_research.to_dict(),
        swot_analysis.to_dict()
    )

    print(f"✓ Executive summary generated")
    print()
    print("Summary Preview:")
    print("-" * 80)
    print(exec_summary[:500])
    print("...")
    print()

    # ===========================
    # Custom Workflow Example
    # ===========================
    print("4. CUSTOM WORKFLOW EXAMPLE")
    print("-" * 80)
    print()

    print("Building custom research workflow...")

    # Step 1: Research competitors
    print("  Step 1: Researching competitors...")
    competitor_research = research_agent.research_competitors(company_name, industry)
    print(f"  ✓ Found {len(competitor_research.findings)} competitors")

    # Step 2: Competitive analysis
    print("  Step 2: Analyzing competition...")
    competitive_analysis = analysis_agent.perform_competitive_analysis(
        company_name,
        company_research.to_dict(),
        competitor_research.to_dict()
    )
    print(f"  ✓ Competitive analysis complete")

    # Step 3: Generate recommendations
    print("  Step 3: Generating recommendations...")
    recommendations = competitive_analysis.recommendations
    print(f"  ✓ Generated {len(recommendations)} recommendations")
    print()

    print("Top Recommendations:")
    for i, rec in enumerate(recommendations[:3], 1):
        print(f"  {i}. {rec}")
    print()

    print("="*80)
    print("EXAMPLE COMPLETE")
    print("="*80)
    print()
    print("This example showed how to:")
    print("  1. Use ResearchAgent for data gathering")
    print("  2. Use AnalysisAgent for strategic analysis")
    print("  3. Use ReportAgent for report generation")
    print("  4. Build custom workflows combining agents")
    print()
    print("You can mix and match agents based on your needs!")
    print()


if __name__ == "__main__":
    main()
