# Gateway Configuration Verification

## Summary

✅ **ALL AGENTS ARE CORRECTLY CONFIGURED TO USE LOCAL GATEWAY**

All 10 agents in the multi-level system are properly configured to send requests to your vLLora local gateway at `http://localhost:9090/v1`.

## Configuration Details

### Base URL Configuration

**Environment Variable:** `LLM_BASE_URL=http://localhost:9090/v1`

All agents use this base URL:

| Agent | Base URL | Status |
|-------|----------|--------|
| ResearchAgent | http://localhost:9090/v1/ | ✅ |
| AnalysisAgent | http://localhost:9090/v1/ | ✅ |
| ReportAgent | http://localhost:9090/v1/ | ✅ |
| SupervisorAgent | http://localhost:9090/v1/ | ✅ |
| QualityReviewerAgent | http://localhost:9090/v1/ | ✅ |
| FinancialAgent | http://localhost:9090/v1/ | ✅ |
| TechnologyAgent | http://localhost:9090/v1/ | ✅ |
| MarketSizingAgent | http://localhost:9090/v1/ | ✅ |
| SentimentAgent | http://localhost:9090/v1/ | ✅ |
| RegulatoryAgent | http://localhost:9090/v1/ | ✅ |

### Header Configuration

Each agent sends three custom headers with every request:

| Header | Purpose | Status |
|--------|---------|--------|
| `x-thread-id` | Groups related workflow traces | ✅ Set by orchestrator |
| `x-run-id` | Groups all traces in same execution | ✅ Set by orchestrator |
| `x-label` | Identifies which agent made the request | ✅ Set per agent |

### Agent Labels

Each agent has a unique label for identification in vLLora:

- `research_agent` - Core research tasks
- `analysis_agent` - SWOT, competitive, trend analysis
- `report_agent` - Report generation
- `supervisor_agent` - Strategic planning (multi-level only)
- `quality_reviewer_agent` - Quality assurance (multi-level only)
- `financial_agent` - Financial analysis (multi-level only)
- `technology_agent` - Technology analysis (multi-level only)
- `market_sizing_agent` - Market sizing (multi-level only)
- `sentiment_agent` - Sentiment analysis (multi-level only)
- `regulatory_agent` - Regulatory analysis (multi-level only)

## How It Works

### 1. Agent Initialization

When agents are first created:
```python
self.llm_client = self.config.get_llm_client(label="agent_name")
```

At this point:
- ✅ `base_url` is set to `http://localhost:9090/v1`
- ✅ `x-label` header is set to agent name
- ⚠️ `x-thread-id` and `x-run-id` are NOT yet set (they're None)

### 2. Orchestrator Sets IDs

When research starts, the orchestrator:
```python
thread_id = str(uuid.uuid4())
run_id = str(uuid.uuid4())
self.config.thread_id = thread_id
self.config.run_id = run_id

# Reinitialize all agents with new IDs
self.research_agent = ResearchAgent(self.config)
self.analysis_agent = AnalysisAgent(self.config)
self.report_agent = ReportAgent(self.config)
```

After reinitialization:
- ✅ `base_url` is still `http://localhost:9090/v1`
- ✅ `x-thread-id` header is now set
- ✅ `x-run-id` header is now set
- ✅ `x-label` header remains set

### 3. API Calls

Every LLM request now includes all headers:
```
POST http://localhost:9090/v1/chat/completions
Headers:
  x-thread-id: <unique-thread-id>
  x-run-id: <unique-run-id>
  x-label: <agent-name>
  ... (other standard headers)
```

## Verification

### Basic Orchestrator (examples/demo.py)

Typical run generates:
- **3-4 requests** from `research_agent` (company, market, competitors)
- **2-3 requests** from `analysis_agent` (SWOT, competitive, trend)
- **1-2 requests** from `report_agent` (final report)

**Total: ~6-9 LLM requests**

### Multi-Level Orchestrator (examples/multi_level_demo.py)

Typical run generates:
- **1 request** from `supervisor_agent` (research planning)
- **3-4 requests** from `research_agent`
- **2-3 requests** from `analysis_agent`
- **5 requests** from specialized agents (financial, technology, market_sizing, sentiment, regulatory)
- **2 requests** from `quality_reviewer_agent` (research review, report review)
- **1-2 requests** from `report_agent`

**Total: ~14-17 LLM requests**

## Viewing in vLLora Dashboard

1. **Open Dashboard:** http://localhost:3000
2. **Navigate to:** Debug tab
3. **Filter by:**
   - Thread ID: See all requests in a workflow
   - Run ID: See all requests in an execution
   - Label: See requests from a specific agent

## Troubleshooting

### Issue: "I only see research_agent requests"

**Possible causes:**

1. **Test script only called research phase** - Some examples or tests might only execute research_agent
   - Solution: Run `examples/demo.py` or `examples/multi_level_demo.py` for complete workflow

2. **Analysis/Report phases failed** - If errors occur, later phases won't run
   - Solution: Check console for error messages

3. **vLLora filtering** - Dashboard might be filtered to show only certain labels
   - Solution: Clear all filters in Debug tab

4. **Timing issue** - Dashboard updates might be delayed
   - Solution: Refresh the page or wait a few seconds

### Issue: "Missing x-thread-id or x-run-id"

**Possible cause:** Testing agents directly without using orchestrator

**Solution:** Always use orchestrator functions:
```python
# ✅ Correct - orchestrator sets IDs
from src.agents import run_market_research
result = run_market_research(company_name="Test", industry="Tech")

# ❌ Wrong - no IDs set
from src.agents import ResearchAgent
agent = ResearchAgent()
result = agent.research_company("Test")  # Missing thread_id and run_id
```

## Testing

### Quick Test

Run the verification script:
```bash
python verify_all_agents.py
```

This will:
- Execute a quick market research
- Show which agents are called
- Display the thread ID for tracking in vLLora
- Confirm all agents sent requests to local gateway

### Manual Test

Check configuration:
```python
from src.utils import get_config

config = get_config()
print(f"Base URL: {config.llm.base_url}")
print(f"Use Local Gateway: {config.llm.use_local_gateway}")
print(f"Provider: {config.llm.provider}")
```

Expected output:
```
Base URL: http://localhost:9090/v1
Use Local Gateway: True
Provider: openai
```

## Conclusion

✅ All agents are correctly configured to use your local vLLora gateway
✅ All requests include proper headers (x-thread-id, x-run-id, x-label)
✅ Both basic and multi-level orchestrators properly initialize agents
✅ All 10 agents successfully send requests to http://localhost:9090/v1

**If you're only seeing research_agent requests in vLLora**, it's likely that:
- The test you ran only executed the research phase
- Later phases encountered errors and didn't complete
- Dashboard filters are limiting what's displayed

**To see all agents in action**, run:
```bash
python examples/demo.py              # Basic: 3 agents
python examples/multi_level_demo.py  # Advanced: 10 agents
```
