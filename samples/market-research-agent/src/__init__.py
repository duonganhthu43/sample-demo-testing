"""
Market Research Agent System
Agentic AI system for comprehensive market research
LLM autonomously decides which tools to invoke via function calling
"""

from .agents import (
    run_agentic_research,
    AgenticOrchestrator,
    ResearchAgent,
    AnalysisAgent,
    ReportAgent,
    TOOL_DEFINITIONS
)

from .utils import get_config

__version__ = "2.0.0"

__all__ = [
    "run_agentic_research",
    "AgenticOrchestrator",
    "ResearchAgent",
    "AnalysisAgent",
    "ReportAgent",
    "TOOL_DEFINITIONS",
    "get_config",
]
