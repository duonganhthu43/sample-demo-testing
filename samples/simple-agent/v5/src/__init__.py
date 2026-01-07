"""
Simple Agent v5 - Semantic Errors for Debug Testing

THIS VERSION HAS INTENTIONAL BUGS FOR TESTING DEBUG TRACING AGENTS.

DO NOT USE IN PRODUCTION - this is for testing/educational purposes only.

Bugs included:
1. Tool name mismatch (search_web vs web_search)
2. Conflicting system prompt instructions
3. Missing response_format for JSON
4. Poor error handling
5. No proper loop termination
"""

from .agent import ResearchAgentV5, ResearchResult, run_research
from .tools import TOOL_DEFINITIONS

__all__ = [
    "ResearchAgentV5",
    "ResearchResult",
    "run_research",
    "TOOL_DEFINITIONS",
]
