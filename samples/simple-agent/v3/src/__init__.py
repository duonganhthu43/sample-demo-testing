"""
Simple Agent v3 - Sub-Agent Architecture

This version improves on v2 with specialized sub-agents:
- PlannerAgent: Decomposes questions and creates research plans
- SearcherAgent: Optimized for web searching
- AnalyzerAgent: Deep analysis of content
- SynthesizerAgent: Combines findings into coherent answers

Same tools as v1/v2 - the improvement is in the architecture.
"""

from .agent import ResearchAgentV3, ResearchResult, run_research
from .tools import TOOL_DEFINITIONS

__all__ = [
    "ResearchAgentV3",
    "ResearchResult",
    "run_research",
    "TOOL_DEFINITIONS",
]
