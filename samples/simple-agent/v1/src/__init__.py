"""
Naive Research Agent (v1) - A simple single-agent research assistant

This is the baseline version demonstrating the core agentic loop pattern.
Later versions will improve on this with better prompting, sub-agents, and parallelism.
"""

from .agent import NaiveResearchAgent, ResearchResult, run_research
from .tools import TOOL_DEFINITIONS

# Backwards compatibility aliases
SimpleAgent = NaiveResearchAgent
run_agent = run_research
AgentResult = ResearchResult

__all__ = [
    "NaiveResearchAgent",
    "ResearchResult",
    "run_research",
    "TOOL_DEFINITIONS",
    # Aliases
    "SimpleAgent",
    "run_agent",
    "AgentResult",
]
