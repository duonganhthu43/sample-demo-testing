# Changelog

## [2.0.0] - 2024-12-16

### 🚀 Major Changes - Pure Agentic Architecture

**Breaking Changes:**
- Removed hard-coded workflow orchestrators
- All research now conducted via LLM function calling
- System autonomously decides which tools to invoke

**Best Practice Implemented:**
- Tools defined ONLY in function calling schema (not duplicated in system prompt)
- System prompt focuses on strategy and decision-making guidelines
- Single source of truth for tool definitions

### ✅ Added

**Agentic Orchestrator:**
- `AgenticOrchestrator` - LLM-driven orchestration class
- `run_agentic_research()` - Primary interface for autonomous research
- `AgenticResult` - Result object with tool call history

**Tool System:**
- 13 tools available for LLM function calling
- `ToolExecutor` - Dispatches tool calls to agents
- `TOOL_DEFINITIONS` - OpenAI function calling schema
- `review_research_quality` - Quality assurance as a tool

**New Tool:** `review_research_quality`
- Allows LLM to invoke quality review when needed
- Multi-dimensional scoring (completeness, accuracy, depth, relevance, clarity)
- Returns feedback for refinement

### ❌ Removed

**Old Orchestrators (completely removed):**
- `MarketResearchOrchestrator` - Use `AgenticOrchestrator` instead
- `MultiLevelOrchestrator` - Use `AgenticOrchestrator` instead
- `run_market_research()` - Use `run_agentic_research()` instead
- `run_multi_level_research()` - Use `run_agentic_research()` instead
- `SupervisorAgent` - No longer needed (LLM makes all decisions)
- `src/agents/orchestrator.py` - Removed
- `src/agents/multi_level_orchestrator.py` - Removed
- `src/agents/supervisor_agent.py` - Removed

**Old Demos (completely removed):**
- Old hard-coded demos removed
- Replaced with agentic demo as primary `examples/demo.py`

### 🔄 Updated

**Core Agents (No Breaking Changes):**
- All core agents still work the same way
- Used as tools by agentic orchestrator
- Can still be used individually

**Documentation:**
- README.md - Updated to focus on agentic approach
- Added MIGRATION_GUIDE.md - Complete migration instructions
- Added AGENTIC_ORCHESTRATOR.md - Detailed documentation
- Updated ORCHESTRATOR_COMPARISON.md - Comparison guide

**Examples:**
- `examples/demo.py` - Now uses agentic orchestrator
- `examples/simple_example.py` - Updated for v2.0
- Old examples preserved as `_deprecated_*.py`

**Package Exports:**
- `src/__init__.py` - Now exports agentic interface
- `src/agents/__init__.py` - Simplified exports
- Version bumped to 2.0.0

### 🎯 Benefits

**Efficiency:**
- 30-67% fewer LLM calls (only necessary tools)
- Adaptive to specific research needs
- No wasted tool invocations

**Flexibility:**
- LLM decides workflow dynamically
- Easy to add new tools
- No hard-coded logic to maintain

**Intelligence:**
- Builds context progressively
- Recognizes when sufficient information gathered
- Strategic tool selection

**Observability:**
- Every tool call traced in vLLora
- Complete visibility into LLM decisions
- Labels: `agentic_orchestrator` + agent labels

### 📊 Performance Comparison

**Before (v1.x) - Hard-coded:**
- Quick: ~6-9 LLM calls
- Standard: ~15-20 LLM calls
- Deep: ~30-40 LLM calls

**After (v2.0) - Agentic:**
- Quick overview: ~3-5 LLM calls (44-67% savings)
- Standard research: ~6-10 LLM calls (40-50% savings)
- Comprehensive: ~10-15 LLM calls (50-63% savings)

### 🔧 Migration

**Before:**
```python
from src import run_market_research
result = run_market_research(company_name="X", depth="deep")
```

**After:**
```python
from src.agents import run_agentic_research
result = run_agentic_research(
    company_name="X",
    objectives=["Detailed analysis", "Report"]
)
```

See [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) for complete instructions.

### 📝 Notes

- **Breaking change:** All old orchestrators completely removed
- No backward compatibility - must migrate to agentic approach
- All core agents remain unchanged
- Individual agent usage still supported
- For old approach, use v1.x

---

## [1.0.0] - 2024-12-15

### Initial Release

**Features:**
- Multi-agent system with ResearchAgent, AnalysisAgent, ReportAgent
- Hard-coded workflow orchestration
- Multi-level orchestrator with supervisor and specialized agents
- Quality reviewer with feedback loops
- 5 specialized agents (Financial, Technology, Market Sizing, Sentiment, Regulatory)
- Full vLLora observability integration
- Web search integration (Tavily)
- Professional report generation

**Orchestration Modes:**
- Basic: Hard-coded workflow
- Multi-level: Hierarchical with supervisor

**Observability:**
- x-thread-id header support
- x-run-id header support
- x-label header support
- vLLora Dashboard integration
