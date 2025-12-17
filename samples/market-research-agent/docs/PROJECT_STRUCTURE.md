# Project Structure - v2.0

## Overview

Clean agentic architecture with no deprecated files. The LLM autonomously decides which tools to invoke.

## Core Files

### `/src/agents/` - Agent System

**Orchestrator:**
- `agentic_orchestrator.py` - LLM-driven orchestration (AgenticOrchestrator, run_agentic_research)
- `tools.py` - Tool definitions and executor (13 tools)

**Core Agents:**
- `research_agent.py` - Company, market, competitor research
- `analysis_agent.py` - SWOT, competitive, trend analysis
- `report_agent.py` - Report generation
- `quality_reviewer.py` - Quality assurance

**Specialized Agents:**
- `specialized_agents.py` - 5 specialized agents:
  - FinancialAgent - Financial analysis
  - TechnologyAgent - Technology assessment
  - MarketSizingAgent - TAM/SAM/SOM
  - SentimentAgent - Customer sentiment
  - RegulatoryAgent - Regulatory analysis

**Module:**
- `__init__.py` - Package exports

### `/src/tools/` - Utilities

- `web_search.py` - Tavily/SerpAPI integration
- `data_extractor.py` - Data extraction utilities
- `visualizer.py` - Visualization helpers

### `/src/utils/` - Configuration

- `config.py` - Configuration management
- `prompts.py` - System prompts for all agents

### `/examples/` - Demonstrations

- `demo.py` - Full agentic demo (primary)
- `simple_example.py` - Quick start example
- `individual_agents.py` - Manual agent usage

### `/outputs/` - Generated Files

- `reports/` - Generated markdown reports
- `logs/` - Application logs (if enabled)

## Documentation

### Main Documentation
- `README.md` - Project overview and quick start
- `AGENTIC_ORCHESTRATOR.md` - Complete agentic guide
- `CHANGELOG.md` - Version history
- `MIGRATION_GUIDE.md` - v1.x to v2.0 migration

### Reference Documentation
- `MULTI_LEVEL_AGENTS.md` - Agent architecture details
- `ORCHESTRATOR_COMPARISON.md` - Architecture comparisons
- `GATEWAY_VERIFICATION.md` - vLLora configuration guide
- `PROJECT_STRUCTURE.md` - This file

## Configuration Files

- `.env` - Environment configuration
- `.env.example` - Example environment file
- `requirements.txt` - Python dependencies

## Architecture Summary

```
User Request
     ↓
AgenticOrchestrator (LLM decides)
     ↓
ToolExecutor (dispatches)
     ↓
Agents (execute)
     ↓
Results (fed back to LLM)
     ↓
LLM decides next step or completes
```

## 13 Available Tools

1. `research_company` → ResearchAgent
2. `research_market` → ResearchAgent
3. `research_competitors` → ResearchAgent
4. `perform_swot_analysis` → AnalysisAgent
5. `perform_competitive_analysis` → AnalysisAgent
6. `perform_trend_analysis` → AnalysisAgent
7. `analyze_financials` → FinancialAgent
8. `analyze_technology` → TechnologyAgent
9. `analyze_market_size` → MarketSizingAgent
10. `analyze_sentiment` → SentimentAgent
11. `analyze_regulatory` → RegulatoryAgent
12. `review_research_quality` → QualityReviewerAgent
13. `generate_report` → ReportAgent

## No Deprecated Files

All hard-coded orchestrators have been **completely removed**:
- ❌ No `orchestrator.py`
- ❌ No `multi_level_orchestrator.py`
- ❌ No `supervisor_agent.py`
- ❌ No `_deprecated_*.py` files

**Clean architecture:** LLM makes all orchestration decisions via function calling.

## Key Changes from v1.x

### Removed
- Hard-coded workflows
- Orchestrator classes with fixed execution paths
- Supervisor agent (LLM now makes strategic decisions)

### Added
- Pure agentic architecture
- 13 tools for LLM function calling
- Autonomous decision-making

### Kept
- All core agents (unchanged)
- All specialized agents (unchanged)
- Quality reviewer (now accessible as tool)
- vLLora observability
- Web search integration

## Usage Patterns

### Primary Usage (Agentic)
```python
from src.agents import run_agentic_research

result = run_agentic_research(
    company_name="X",
    objectives=["analysis goals"]
)
```

### Individual Agents
```python
from src.agents import ResearchAgent, AnalysisAgent
from src.utils import get_config

config = get_config()
research = ResearchAgent(config)
analysis = AnalysisAgent(config)

# Use agents directly for custom workflows
```

## Observability

**vLLora Dashboard:** http://localhost:3000

**Headers on every request:**
- `x-thread-id` - Workflow grouping
- `x-run-id` - Execution grouping
- `x-label` - Agent identification

**Labels:**
- `agentic_orchestrator` - Orchestration decisions
- `research_agent` - Research tasks
- `analysis_agent` - Analysis tasks
- `financial_agent` - Financial analysis
- `technology_agent` - Technology analysis
- `market_sizing_agent` - Market sizing
- `sentiment_agent` - Sentiment analysis
- `regulatory_agent` - Regulatory analysis
- `quality_reviewer_agent` - Quality review
- `report_agent` - Report generation

## File Count Summary

**Agents:** 8 files (orchestrator + tools + 6 agent files)
**Examples:** 3 files
**Total Python files:** ~20 files
**Documentation:** 8 markdown files

**Clean, focused architecture with no legacy code.**
