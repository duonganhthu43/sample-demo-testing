"""
Simple Agent v4 - Parallel Execution

This version improves on v3 with parallel execution:
- Multiple searches executed concurrently
- Parallel content extraction
- Faster overall research time

Same sub-agent architecture as v3, but with concurrent tool execution.
"""

from .agent import ResearchAgentV4, ResearchResult, run_research
from .tools import TOOL_DEFINITIONS

__all__ = [
    "ResearchAgentV4",
    "ResearchResult",
    "run_research",
    "TOOL_DEFINITIONS",
]
