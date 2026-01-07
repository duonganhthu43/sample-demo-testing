"""
Simple Agent v2 - Improved Prompting

This version improves on v1 with:
- Query decomposition (breaks complex questions into sub-questions)
- Chain-of-thought reasoning
- Better search query formulation
- Structured thinking process

Same tools as v1 - the improvement is in the prompting, not the tools.
"""

from .agent import ResearchAgentV2, ResearchResult, run_research
from .tools import TOOL_DEFINITIONS

__all__ = [
    "ResearchAgentV2",
    "ResearchResult",
    "run_research",
    "TOOL_DEFINITIONS",
]
