"""
Agents Module
Tool-based agentic system for market research
All agents are invoked as tools via LLM function calling
"""

# Core agents (used as tools by agentic orchestrator)
from .research_agent import ResearchAgent, ResearchResult
from .analysis_agent import AnalysisAgent, AnalysisResult
from .report_agent import ReportAgent, Report
from .quality_reviewer import QualityReviewerAgent, QualityReview, QualityScore
from .specialized_agents import (
    FinancialAgent,
    TechnologyAgent,
    MarketSizingAgent,
    SentimentAgent,
    RegulatoryAgent,
    SpecializedResult
)

# Agentic orchestrator (primary interface)
from .agentic_orchestrator import AgenticOrchestrator, AgenticResult, run_agentic_research
from .tools import TOOL_DEFINITIONS, ToolExecutor

__all__ = [
    # Core agents
    "ResearchAgent",
    "ResearchResult",
    "AnalysisAgent",
    "AnalysisResult",
    "ReportAgent",
    "Report",
    "QualityReviewerAgent",
    "QualityReview",
    "QualityScore",
    "FinancialAgent",
    "TechnologyAgent",
    "MarketSizingAgent",
    "SentimentAgent",
    "RegulatoryAgent",
    "SpecializedResult",
    # Agentic orchestrator (primary interface)
    "AgenticOrchestrator",
    "AgenticResult",
    "run_agentic_research",
    "TOOL_DEFINITIONS",
    "ToolExecutor",
]
