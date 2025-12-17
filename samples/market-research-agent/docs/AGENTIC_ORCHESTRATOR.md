# Agentic Orchestrator - LLM-Driven Function Calling

## Overview

The **Agentic Orchestrator** represents a paradigm shift in how the market research system operates. Instead of following hard-coded workflows, the LLM autonomously decides which research tools to invoke, in what order, and when to stop.

## Key Concept

### Traditional Approach (Orchestrator)
```python
# Hard-coded workflow
1. research_agent.research_company()
2. research_agent.research_market()
3. research_agent.research_competitors()
4. analysis_agent.perform_swot_analysis()
5. analysis_agent.perform_competitive_analysis()
6. report_agent.generate_report()
```

**Problem:** Rigid, one-size-fits-all approach

### Agentic Approach (LLM-Driven)
```python
# LLM decides the workflow
LLM: "I need to understand the company first"
  → calls research_company()

LLM: "Now I should analyze the market"
  → calls research_market()

LLM: "Let me get competitor information"
  → calls research_competitors()

LLM: "I have enough data for SWOT"
  → calls perform_swot_analysis()

LLM: "Financial deep-dive would be valuable here"
  → calls analyze_financials()

LLM: "I have sufficient information now"
  → calls generate_report()
  → provides summary and stops
```

**Benefits:**
- Adaptive to specific research needs
- Efficient (only calls necessary tools)
- Self-orchestrating (no hard-coded logic)
- Intelligent (builds context progressively)

## Architecture

```
┌─────────────────────────────────────────────────────┐
│            AGENTIC ORCHESTRATOR                     │
│  (LLM with Function Calling Capabilities)           │
└─────────────────┬───────────────────────────────────┘
                  │
                  │ Decides which tools to call
                  │
    ┌─────────────┴─────────────┐
    │                           │
    ▼                           ▼
┌────────────────┐      ┌──────────────────┐
│  TOOL EXECUTOR │      │ TOOL DEFINITIONS │
│                │      │                  │
│ Dispatches     │◄─────┤ 12 Tools:        │
│ tool calls     │      │ - research_*     │
│ to agents      │      │ - perform_*      │
│                │      │ - analyze_*      │
│                │      │ - generate_*     │
└────────┬───────┘      └──────────────────┘
         │
         │ Invokes actual agent methods
         │
    ┌────┴───────────────────────────────────┐
    │                                        │
    ▼                                        ▼
┌─────────────┐  ┌──────────────┐  ┌────────────────┐
│  Research   │  │  Analysis    │  │  Specialized   │
│  Agent      │  │  Agent       │  │  Agents        │
└─────────────┘  └──────────────┘  └────────────────┘
```

## How It Works

### 1. Tool Definitions

13 tools are exposed to the LLM via OpenAI function calling (not listed in system prompt - defined in `tools` parameter):

| Tool | Purpose | Agent |
|------|---------|-------|
| `research_company` | Company research | ResearchAgent |
| `research_market` | Market/industry research | ResearchAgent |
| `research_competitors` | Competitor analysis | ResearchAgent |
| `perform_swot_analysis` | SWOT analysis | AnalysisAgent |
| `perform_competitive_analysis` | Competitive positioning | AnalysisAgent |
| `perform_trend_analysis` | Market trends | AnalysisAgent |
| `analyze_financials` | Financial deep-dive | FinancialAgent |
| `analyze_technology` | Technology analysis | TechnologyAgent |
| `analyze_market_size` | TAM/SAM/SOM | MarketSizingAgent |
| `analyze_sentiment` | Customer sentiment | SentimentAgent |
| `analyze_regulatory` | Regulatory landscape | RegulatoryAgent |
| `generate_report` | Final report | ReportAgent |

### 2. Agentic Loop

```
1. User provides research request
   ↓
2. LLM receives request + tool definitions
   ↓
3. LLM decides: "I should call tool X with args Y"
   ↓
4. ToolExecutor dispatches call to appropriate agent
   ↓
5. Agent executes and returns result
   ↓
6. Result fed back to LLM
   ↓
7. LLM evaluates: "Do I need more information?"
   ├─ YES → Go to step 3 (call another tool)
   └─ NO → Provide summary and finish
```

### 3. Design Decision: Tools in Function Calling Schema Only

**Important:** Tools are defined **only** in the OpenAI `tools` parameter, not in the system prompt.

**Why?**
- ✅ Avoids redundancy - LLM already sees tools via function calling
- ✅ Single source of truth - tool definitions in one place
- ✅ Cleaner prompts - focuses on strategy, not tool listings
- ✅ Easier maintenance - update tools in one location

**System prompt focuses on:**
- Strategic approach and guidelines
- Decision-making criteria
- Best practices for tool selection

**Tools are automatically visible to the LLM via the `tools` parameter in the API call.**

### 4. Context Management

The `ToolExecutor` maintains context across tool calls:

```python
context = {
    "research": [result1, result2, ...],      # From research tools
    "analysis": [result3, result4, ...],      # From analysis tools
    "specialized": [result5, result6, ...]    # From specialized tools
}
```

Later tool calls have access to earlier results, enabling:
- Progressive context building
- Informed decision making
- Comprehensive synthesis

## Usage

### Basic Usage

```python
from src.agents import run_agentic_research

result = run_agentic_research(
    company_name="Stripe",
    industry="Fintech",
    objectives=[
        "Analyze competitive position",
        "Evaluate technology capabilities",
        "Assess market opportunities"
    ],
    max_iterations=20
)

print(f"Tools called: {len(result.tool_calls_made)}")
print(f"Duration: {result.total_duration:.2f}s")
```

### Advanced Usage

```python
from src.agents import AgenticOrchestrator
from src.utils import get_config

config = get_config()
orchestrator = AgenticOrchestrator(config, max_iterations=25)

result = orchestrator.execute_research(
    company_name="OpenAI",
    industry="AI/ML",
    objectives=["Comprehensive market analysis"],
    additional_instructions="Focus on AI safety and responsible AI practices"
)

# Analyze what the LLM decided to do
for tc in result.tool_calls_made:
    print(f"Iteration {tc['iteration']}: {tc['tool']}")
```

### Custom Tool Selection

The LLM will strategically select tools based on:

1. **User objectives** - What was requested
2. **Information gaps** - What's still unknown
3. **Context** - What has already been gathered
4. **Relevance** - What's most valuable

Example: For "quick competitor overview", LLM might call:
- `research_company` (understand the target)
- `research_competitors` (identify competitors)
- `perform_competitive_analysis` (compare positioning)
- `generate_report` (create deliverable)

But for "comprehensive investment analysis", LLM might call:
- All research tools
- All analysis tools
- All specialized tools (financials, technology, market sizing, etc.)
- Quality review
- Report generation

## Benefits

### 1. Adaptive Workflow
✅ LLM tailors research to specific needs
✅ No wasted calls on irrelevant tools
✅ Depth adjusts based on objectives

### 2. Intelligent Decision Making
✅ LLM sequences tools logically
✅ Builds context progressively
✅ Recognizes when sufficient information is gathered

### 3. Self-Orchestration
✅ No hard-coded workflow logic
✅ System manages itself
✅ Easy to extend with new tools

### 4. Observability
✅ All tool calls visible in vLLora Dashboard
✅ Each tool labeled with agent name
✅ Complete trace of LLM decision-making

## Comparison with Other Orchestrators

| Feature | Basic Orchestrator | Multi-Level Orchestrator | Agentic Orchestrator |
|---------|-------------------|-------------------------|---------------------|
| **Workflow** | Hard-coded | Hard-coded hierarchical | LLM-driven |
| **Flexibility** | Low | Medium | High |
| **Tool Selection** | All tools always | Supervisor selects | LLM selects |
| **Adaptability** | None | Some (via supervisor) | Full |
| **Efficiency** | Medium | Medium-High | High |
| **Complexity** | Low | High | Medium |
| **Best For** | Simple workflows | Complex multi-phase | Autonomous research |

## Performance

### Expected Behavior

**Quick Research Request:**
- LLM typically calls: 3-5 tools
- Duration: 1-3 minutes
- Example: company + market + SWOT + report

**Standard Research Request:**
- LLM typically calls: 6-10 tools
- Duration: 3-7 minutes
- Example: research phase + analysis phase + 1-2 specialized + report

**Deep Research Request:**
- LLM typically calls: 10-15 tools
- Duration: 8-15 minutes
- Example: full research + full analysis + all specialized + report

### Efficiency Gains

Compared to always calling all tools:

| Scenario | All Tools | Agentic | Savings |
|----------|-----------|---------|---------|
| Quick overview | 12 tools | 4 tools | 67% |
| Competitor analysis | 12 tools | 6 tools | 50% |
| Investment DD | 12 tools | 11 tools | 8% |

## Observability

### vLLora Dashboard

All tool calls are traced with headers:

```
x-thread-id: <unique-thread-id>
x-run-id: <unique-run-id>
x-label: agentic_orchestrator
```

When tools invoke agents, you'll also see:
- `x-label: research_agent`
- `x-label: analysis_agent`
- `x-label: financial_agent`
- etc.

### Example Trace

```
1. [agentic_orchestrator] Initial planning
2. [research_agent] research_company for "Stripe"
3. [agentic_orchestrator] Decide next step
4. [research_agent] research_market for "Fintech"
5. [agentic_orchestrator] Decide next step
6. [analysis_agent] perform_swot_analysis
7. [agentic_orchestrator] Decide next step
8. [financial_agent] analyze_financials
9. [agentic_orchestrator] Decide next step
10. [report_agent] generate_report
11. [agentic_orchestrator] Final summary
```

## Adding New Tools

To add a new tool:

### 1. Define Tool in `tools.py`

```python
{
    "type": "function",
    "function": {
        "name": "analyze_partnerships",
        "description": "Analyze strategic partnerships and ecosystem",
        "parameters": {
            "type": "object",
            "properties": {
                "company_name": {
                    "type": "string",
                    "description": "Company to analyze"
                }
            },
            "required": ["company_name"]
        }
    }
}
```

### 2. Implement in ToolExecutor

```python
def execute_tool(self, tool_name: str, arguments: Dict[str, Any]):
    # ... existing code ...

    elif tool_name == "analyze_partnerships":
        agent = self._get_partnerships_agent()
        result = agent.analyze_partnerships(
            company_name=arguments["company_name"]
        )
        return {"success": True, "result": result.to_dict()}
```

### 3. Create Agent (if needed)

```python
class PartnershipsAgent:
    def analyze_partnerships(self, company_name: str):
        # Implementation
        pass
```

That's it! The LLM will automatically discover and use the new tool.

## Best Practices

### 1. Clear Objectives
✅ Provide specific research goals
❌ Don't use vague requests

```python
# Good
objectives = [
    "Analyze Stripe's competitive moat in payment processing",
    "Evaluate their technology differentiation"
]

# Bad
objectives = ["Research Stripe"]
```

### 2. Appropriate Iteration Limits
- Quick research: `max_iterations=10`
- Standard research: `max_iterations=20`
- Deep research: `max_iterations=30`

### 3. Monitor Tool Calls
Check what the LLM is calling to understand its strategy:

```python
result = run_agentic_research(...)

for tc in result.tool_calls_made:
    print(f"{tc['tool']} → {tc['result']['success']}")
```

### 4. Provide Context
Use `additional_instructions` for specific guidance:

```python
run_agentic_research(
    company_name="Anthropic",
    additional_instructions="Focus on AI safety and constitutional AI"
)
```

## Troubleshooting

### LLM Calls Too Many Tools

**Cause:** Overly broad objectives
**Solution:** Be more specific about what you need

### LLM Calls Too Few Tools

**Cause:** Vague request or early stopping
**Solution:** Provide detailed objectives, increase max_iterations

### Tool Execution Errors

**Cause:** Missing data or API failures
**Solution:** Check console logs for specific errors

### LLM Never Stops

**Cause:** max_iterations reached
**Solution:** Increase limit or simplify objectives

## Summary

The Agentic Orchestrator represents the future of market research automation:

✅ **Autonomous** - LLM drives the workflow
✅ **Adaptive** - Tailors approach to each request
✅ **Efficient** - Only calls necessary tools
✅ **Intelligent** - Makes strategic decisions
✅ **Observable** - Full tracing in vLLora
✅ **Extensible** - Easy to add new tools

**Run the demo:**
```bash
python examples/agentic_demo.py
```

Watch the LLM orchestrate itself!
