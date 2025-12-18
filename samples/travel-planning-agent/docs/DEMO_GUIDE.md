# Travel Planning Agent - Demo & Verification Guide

This guide provides step-by-step instructions for running the Travel Planning Agent demo and verifying LLM calls using vLLora MCP.

## Prerequisites

### 1. vLLora Gateway Running

Ensure vLLora is running and accessible:

```bash
# Check if vLLora is running
curl http://localhost:9090/health

# vLLora Dashboard should be at
# http://localhost:3000
```

### 2. Environment Setup

```bash
cd samples/travel-planning-agent

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# or: .\venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
```

### 3. Required Dependencies

The demo requires these key packages:

```bash
pip install openai anthropic tavily-python pillow requests
```

### 4. Configure .env

Edit `.env` with your settings:

```env
# LLM Gateway (vLLora)
LLM_BASE_URL=http://localhost:9090/v1
OPENAI_API_KEY=dummy-key  # vLLora handles the actual key
OPENAI_MODEL=gpt-4o-mini  # or gpt-4-turbo-preview

# Search API (for real searches)
TAVILY_API_KEY=tvly-your-key

# Or enable mock mode (no external API calls)
MOCK_EXTERNAL_APIS=true
```

## Running the Demo

### Option 1: With Tavily (Real Search)

```bash
cd samples/travel-planning-agent
source venv/bin/activate
python examples/demo.py
```

### Option 2: Mock Mode (No API Keys)

Set `MOCK_EXTERNAL_APIS=true` in `.env`, then:

```bash
python examples/demo.py
```

### Expected Output

```
================================================================================
               TRAVEL PLANNING AGENT DEMO
               LLM-Driven Function Calling
                    Powered by vLLora
================================================================================

Starting travel planning (thread: <uuid>)

--- Iteration 1 ---
  tool_choice: required
>>> Executing tool: research_destination with args: ['destination']
...

--- Iteration N ---
Planning complete - no more tool calls

================================================================================
TRAVEL PLANNING RESULTS
================================================================================

Execution Summary:
  Total Duration: ~200s
  Iterations: 10-15
  Tools Called: 15-20

Tool Usage Details:
  - research_destination: 1 call(s)
  - research_flights: 1-2 call(s)
  - research_accommodations: 1 call(s)
  ...

Generated Itinerary:
  Destination: Tokyo
  Days: 5
  Estimated Cost: $650.0
```

## Verifying with vLLora MCP

The vLLora MCP provides tools to inspect and verify LLM calls made during the demo.

### Tool 1: Get Recent Stats

Get an aggregated overview of LLM and tool calls from the last N minutes:

```json
{
  "tool": "mcp__vllora-mcp__get_recent_stats",
  "arguments": {
    "last_n_minutes": 30
  }
}
```

**What to look for:**
- Total LLM calls count
- Tool call distribution
- Response times
- Error rates

### Tool 2: Search Traces

Search for specific traces with filters:

```json
{
  "tool": "mcp__vllora-mcp__search_traces",
  "arguments": {
    "time_range": {
      "last_n_minutes": 30
    },
    "filters": {
      "operation_name": "llm_call"
    },
    "include": {
      "metrics": true,
      "tokens": true,
      "costs": true,
      "output": true
    },
    "page": {
      "limit": 20
    }
  }
}
```

**Filter by label to see specific agents:**

```json
{
  "filters": {
    "labels": {
      "label": "travel_orchestrator"
    }
  }
}
```

Available labels in this demo:
- `travel_orchestrator` - Main agentic loop decisions
- `research_agent` - Destination/flight/hotel/activity research
- `analysis_agent` - Feasibility, cost, schedule analysis
- `budget_agent` - Budget optimization
- `weather_agent` - Weather forecasting
- `safety_agent` - Safety analysis
- `transport_agent` - Local transport info
- `itinerary_agent` - Itinerary generation
- `presentation_agent` - Markdown formatting

### Tool 3: Get Run Overview

Get high-level overview of a specific run:

```json
{
  "tool": "mcp__vllora-mcp__get_run_overview",
  "arguments": {
    "run_id": "<run_id_from_search_traces>"
  }
}
```

### Tool 4: Get LLM Call Details

Get detailed information about a specific LLM call:

```json
{
  "tool": "mcp__vllora-mcp__get_llm_call",
  "arguments": {
    "trace_id": "<trace_id>",
    "span_id": "<span_id>",
    "allow_unsafe_text": true,
    "include": {
      "llm_payload": true,
      "unsafe_text": true
    }
  }
}
```

**What to verify:**
- System prompts are correct
- User content is structured array format (optimization check)
- Tool definitions are passed correctly
- Response contains expected tool calls or content
- `response_format` contains JSON schema (for structured output calls)

## Verification Checklist

### 1. Structured Content Format

Check that user messages use array format instead of string concatenation:

```json
{
  "role": "user",
  "content": [
    {"type": "text", "text": "## Trip Details\n\n```json\n{...}\n```"},
    {"type": "text", "text": "## Constraints\n\n```json\n{...}\n```"},
    {"type": "text", "text": "## Task\n\nGenerate..."}
  ]
}
```

### 2. Structured Outputs (JSON Schema)

Verify that agents using structured outputs include `response_format` in their LLM calls:

```json
{
  "response_format": {
    "type": "json_schema",
    "json_schema": {
      "name": "itinerary",
      "schema": {...},
      "strict": true
    }
  }
}
```

**Agents using structured outputs:**
- `itinerary_agent` → `ITINERARY_SCHEMA`
- `research_agent` (destination) → `DESTINATION_EXTRACTION_SCHEMA`
- `weather_service` → `WEATHER_FORECAST_SCHEMA`

**How to verify:**
1. Use `get_llm_call` with `include.llm_payload: true`
2. Check the request contains `response_format` with `type: "json_schema"`
3. Verify response is valid JSON matching the schema

### 3. Image Handling

After running demo, check console output for:

```
Built image registry with N images
Replaced M image placeholders with actual images
Warning: X placeholders not matched: [...]
```

### 4. Tool Call Flow

Expected tool call sequence:
1. `research_destination` - First call
2. `research_flights`, `research_accommodations`, `research_activities` - Parallel
3. `analyze_weather`, `analyze_safety`, `analyze_local_transport`, `analyze_cost_breakdown`, `analyze_itinerary_feasibility` - Parallel
4. `optimize_budget` - After cost analysis
5. `analyze_schedule_optimization` - After feasibility
6. `generate_itinerary` - Main itinerary
7. `generate_summary` - Trip summary
8. `format_presentation` - Final markdown

### 5. Context Accumulation

Verify that later agents receive context from earlier tools:
- `analyze_cost_breakdown` should see flight/hotel/activity prices
- `generate_itinerary` should see all research and analysis results
- `format_presentation` should see complete itinerary with images

## Troubleshooting

### "No module named 'tavily'"

```bash
pip install tavily-python
```

### "TAVILY_API_KEY is required"

Either:
1. Add `TAVILY_API_KEY=tvly-xxx` to `.env`
2. Or set `MOCK_EXTERNAL_APIS=true`

### vLLora Connection Error

```bash
# Check vLLora is running
curl http://localhost:9090/health

# Check MCP server
curl http://localhost:3000/api/health
```

### Structured Output Schema Error

If you see errors like:
```
Invalid schema for response_format 'itinerary': Missing 'field_name' in required array
```

This means a property in the schema is not listed in the `required` array. OpenAI's strict mode requires ALL properties to be in `required`. Fix by updating `src/utils/schemas.py`.

### Image Placeholders Not Matching

The demo logs show unmatched placeholders. This is expected behavior - unmatched placeholders get SVG fallbacks:

```
Warning: 4 placeholders not matched: ['sensoji_temple', ...]
Available registry keys: ['hero', '50_mustsee_tourist_attractions...']
```

The mismatch occurs because:
- LLM generates semantic names (`sensoji_temple`)
- Registry has Tavily result titles (`50_mustsee_tourist_attractions...`)

Both work - matched get real images, unmatched get styled SVG placeholders.

## Example Verification Session

```bash
# 1. Run the demo
cd samples/travel-planning-agent
source venv/bin/activate
python examples/demo.py

# 2. Note the thread ID from output:
# Starting travel planning (thread: abc123-...)

# 3. Use vLLora MCP to verify (in Claude Code):
# - Call search_traces with last_n_minutes: 10
# - Look for traces with thread_id matching
# - Inspect specific LLM calls to verify structured content format
```

## Performance Benchmarks

Typical demo execution:
- **Duration**: 150-250 seconds
- **Iterations**: 8-12
- **LLM Calls**: 15-25
- **Total Tokens**: 50,000-100,000
- **Tool Calls**: 15-20

## Related Documentation

- [README.md](../README.md) - Project overview
- [ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture (includes Structured Outputs section)
- [schemas.py](../src/utils/schemas.py) - JSON schemas for structured outputs
- vLLora docs at http://localhost:3000/docs
