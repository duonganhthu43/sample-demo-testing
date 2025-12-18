# Travel Planning Agent

An autonomous travel planning system that uses LLM function calling to create comprehensive travel itineraries.

## Overview

This agent demonstrates production-ready agentic AI patterns for travel planning:

- **Autonomous Decision Making**: LLM decides which tools to use and in what order
- **13 Specialized Tools**: Research, analysis, and planning capabilities
- **Parallel Execution**: Tools run concurrently for faster results
- **Context Accumulation**: Results build on each other
- **Mock Mode**: Works without real API keys for testing

## Quick Start

```bash
# Setup
./setup.sh

# Or manually:
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# Run demo
cd examples
python demo.py
```

## Usage

### With JSON Configuration

```bash
# Using config file
python demo.py travel_config.json

# Using JSON string
python demo.py '{"task": "Plan a 3-day trip to Tokyo", "constraints": {"budget": "under $1000"}}'
```

### JSON Schema

```json
{
  "task": "Plan a 5-day trip to Tokyo in April",
  "constraints": {
    "budget": "under $1500 total",
    "departure_city": "Singapore",
    "travel_dates": "April 10-15",
    "preferences": [
      "avoid overnight flights",
      "hotel near public transport",
      "no more than 2 activities per day"
    ],
    "hard_constraints": [
      "must arrive before 6pm local time",
      "return flight must be direct"
    ]
  },
  "max_iterations": 20
}
```

### Programmatic Usage

```python
from src.agents import run_travel_planning

result = run_travel_planning(
    task="Plan a 5-day trip to Tokyo",
    constraints={
        "budget": "under $1500",
        "departure_city": "Singapore",
        "travel_dates": "April 10-15"
    }
)

print(f"Itinerary generated: {result.itinerary}")
```

## Available Tools

### Research Tools
| Tool | Description |
|------|-------------|
| `research_destination` | Destination overview, visa, culture, tips |
| `research_flights` | Search available flights |
| `research_accommodations` | Search hotels and hostels |
| `research_activities` | Find attractions and activities |

### Analysis Tools
| Tool | Description |
|------|-------------|
| `analyze_itinerary_feasibility` | Check if plan is realistic |
| `analyze_cost_breakdown` | Detailed budget analysis |
| `analyze_schedule_optimization` | Optimize daily schedule |

### Specialized Tools
| Tool | Description |
|------|-------------|
| `optimize_budget` | Find budget-friendly alternatives |
| `analyze_weather` | Weather forecast and packing tips |
| `analyze_safety` | Safety info and warnings |
| `analyze_local_transport` | Local transport options |

### Output Tools
| Tool | Description |
|------|-------------|
| `generate_itinerary` | Create day-by-day itinerary |
| `generate_summary` | Trip summary and checklist |

## Architecture

```
┌─────────────────────────────────────────┐
│         User Request (JSON)             │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│      Travel Planning Orchestrator       │
│      (LLM with function calling)        │
└────────────────┬────────────────────────┘
                 │
    ┌────────────┴────────────┐
    │                         │
    ▼                         ▼
┌─────────────────┐   ┌──────────────────┐
│  RESEARCH TOOLS │   │  ANALYSIS TOOLS  │
├─────────────────┤   ├──────────────────┤
│ Destination     │   │ Feasibility      │
│ Flights         │   │ Cost Breakdown   │
│ Hotels          │   │ Schedule Opt.    │
│ Activities      │   └──────────────────┘
└─────────────────┘
    │                         │
    ▼                         ▼
┌─────────────────┐   ┌──────────────────┐
│ SPECIALIZED     │   │  OUTPUT TOOLS    │
├─────────────────┤   ├──────────────────┤
│ Budget Agent    │   │ Itinerary Gen.   │
│ Weather Agent   │   │ Summary Gen.     │
│ Safety Agent    │   └──────────────────┘
│ Transport Agent │
└─────────────────┘
```

## Configuration

Edit `.env` to configure:

```env
# LLM Provider
LLM_PROVIDER=openai
OPENAI_BASE_URL=http://localhost:9090/v1
OPENAI_API_KEY=dummy-key
OPENAI_MODEL=gpt-4-turbo-preview

# Search (optional - uses mock if not set)
TAVILY_API_KEY=tvly-your-key

# Agent settings
MAX_ITERATIONS=20
```

## Project Structure

```
travel-planning-agent/
├── src/
│   ├── agents/
│   │   ├── agentic_orchestrator.py  # Main LLM orchestrator
│   │   ├── research_agent.py        # Research tools
│   │   ├── analysis_agent.py        # Analysis tools
│   │   ├── specialized_agents.py    # Budget, weather, safety, transport
│   │   ├── itinerary_agent.py       # Itinerary generation
│   │   └── tools.py                 # Tool definitions & executor
│   ├── tools/
│   │   ├── flight_search.py         # Flight search (mock)
│   │   ├── hotel_search.py          # Hotel search (mock)
│   │   ├── activity_search.py       # Activity search (mock)
│   │   └── weather_service.py       # Weather service (mock)
│   └── utils/
│       ├── config.py                # Configuration
│       └── prompts.py               # System prompts
├── examples/
│   ├── demo.py                      # Main demo
│   └── travel_config.json           # Sample config
└── docs/
    ├── ARCHITECTURE.md              # Architecture details
    └── DEMO_GUIDE.md                # Demo & vLLora verification guide
```

## Observability

With vLLora, view all LLM calls at `http://localhost:3000`:

- `x-thread-id`: Groups all calls for one planning session
- `x-run-id`: Unique ID for each run
- `x-label`: Identifies which agent made the call

### vLLora MCP Verification

Use vLLora MCP tools to verify LLM calls programmatically:

```json
// Get recent stats
{"tool": "mcp__vllora-mcp__get_recent_stats", "arguments": {"last_n_minutes": 30}}

// Search traces by label
{"tool": "mcp__vllora-mcp__search_traces", "arguments": {
  "filters": {"labels": {"label": "travel_orchestrator"}},
  "include": {"metrics": true, "tokens": true}
}}

// Get detailed LLM call
{"tool": "mcp__vllora-mcp__get_llm_call", "arguments": {
  "trace_id": "...", "span_id": "...", "allow_unsafe_text": true
}}
```

See [docs/DEMO_GUIDE.md](docs/DEMO_GUIDE.md) for complete verification instructions.

## License

MIT
