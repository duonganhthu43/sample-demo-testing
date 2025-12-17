# Travel Planning Agent Architecture

## Overview

The Travel Planning Agent is built on an **agentic orchestration pattern** where a central LLM orchestrator autonomously decides which tools to invoke to complete a travel planning task.

## Core Design Principles

### 1. Single Agentic Loop
Instead of nested agent loops (which are slow), we use a single orchestrator that makes all decisions:

```
Orchestrator (agentic) → Tools (deterministic) → Orchestrator → Tools → ...
```

### 2. Deterministic Sub-Agents
Each tool/agent performs a **fixed, predictable operation**:
- No internal LLM loops
- One task, one result
- Easily testable

### 3. Parallel Execution
Tools can run concurrently using `ThreadPoolExecutor` when they don't depend on each other.

## Component Architecture

### Agentic Orchestrator

```python
class TravelPlanningOrchestrator:
    """Main orchestrator using LLM function calling"""

    def plan_trip(self, task, constraints, max_iterations):
        messages = [system_prompt, user_prompt]

        while iteration < max_iterations:
            response = llm.chat(messages, tools=TOOL_DEFINITIONS)

            if response.tool_calls:
                # Execute tools (parallel if enabled)
                results = execute_tools(response.tool_calls)
                # Add results to conversation
                messages.extend(tool_results)
            else:
                # LLM is done - no more tool calls
                break

        return TravelPlanResult(...)
```

### Tool Definitions

Tools are defined using OpenAI function calling format:

```python
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "research_flights",
            "description": "Search for available flights...",
            "parameters": {
                "type": "object",
                "properties": {
                    "origin": {"type": "string"},
                    "destination": {"type": "string"},
                    "departure_date": {"type": "string"}
                },
                "required": ["origin", "destination", "departure_date"]
            }
        }
    },
    # ... 12 more tools
]
```

### Tool Executor

Routes tool calls to appropriate agents:

```python
class ToolExecutor:
    def execute_tool(self, tool_name, arguments):
        if tool_name == "research_flights":
            return self._research_agent.research_flights(**arguments)
        elif tool_name == "analyze_weather":
            return self._weather_agent.analyze_weather(**arguments)
        # ...
```

### Context Accumulation

Results are stored and available to subsequent tools:

```python
self.context = {
    "destination": "Tokyo",
    "travel_dates": "April 10-15",
    "research": [
        {"type": "destination", ...},
        {"type": "flights", ...},
        {"type": "hotels", ...}
    ],
    "analysis": [
        {"type": "feasibility", ...},
        {"type": "cost", ...}
    ],
    "specialized": [
        {"type": "weather", ...},
        {"type": "safety", ...}
    ]
}
```

## Data Flow

```
1. User Input (JSON)
   │
   ├─ task: "Plan a 5-day trip to Tokyo"
   └─ constraints: {budget, dates, preferences, hard_constraints}

2. Orchestrator Initialization
   │
   ├─ Generate thread_id, run_id (for tracing)
   ├─ Extract destination, dates, budget from input
   └─ Set initial context

3. Agentic Loop
   │
   ├─ Iteration 1: LLM calls research_destination
   │   └─ Result: destination info, visa, culture tips
   │
   ├─ Iteration 2: LLM calls research_flights, research_accommodations
   │   └─ Results: flight options, hotel options (parallel)
   │
   ├─ Iteration 3: LLM calls research_activities
   │   └─ Result: attractions, activities list
   │
   ├─ Iteration 4: LLM calls analyze_weather, analyze_safety
   │   └─ Results: forecast, safety tips (parallel)
   │
   ├─ Iteration 5: LLM calls analyze_cost_breakdown
   │   └─ Result: budget analysis
   │
   ├─ Iteration 6: LLM calls generate_itinerary
   │   └─ Result: day-by-day itinerary
   │
   └─ Iteration 7: LLM stops (no more tool calls)

4. Result Assembly
   │
   └─ TravelPlanResult with itinerary, costs, all context
```

## Agent Design Pattern

Each agent follows this pattern:

```python
@dataclass
class AgentResult:
    """Structured result"""
    field1: str
    field2: List[Dict]

    def to_dict(self) -> Dict:
        return {...}

class Agent:
    def __init__(self, config):
        self.config = config
        # Initialize tools, clients

    def execute_task(self, **kwargs) -> AgentResult:
        # Deterministic execution
        # NO internal LLM loops
        return AgentResult(...)
```

## Observability

All LLM calls include tracing headers:

```python
headers = {
    "x-thread-id": "travel-abc123",  # Groups all calls in session
    "x-run-id": "run-xyz789",        # Unique per run
    "x-label": "research_agent"       # Identifies the agent
}
```

View in vLLora dashboard at `http://localhost:3000`

## Configuration System

Uses Pydantic for type-safe configuration:

```python
class Config:
    llm: LLMConfig        # Provider, API keys, model
    search: SearchConfig  # Search API keys
    agent: AgentConfig    # Max iterations, parallel execution
    app: AppConfig        # Logging, output dir, mock mode
```

## Mock Mode

All tools have mock implementations that return realistic data:

- **FlightSearchTool**: Generates mock flights with realistic airlines, times, prices
- **HotelSearchTool**: Returns mock hotels with ratings, amenities
- **ActivitySearchTool**: Provides real Tokyo activities (or generic for other cities)
- **WeatherService**: Generates seasonal weather forecasts

This allows the demo to work without any real API keys.

## Key Files

| File | Purpose |
|------|---------|
| `src/agents/agentic_orchestrator.py` | Main LLM orchestrator |
| `src/agents/tools.py` | Tool definitions (13 tools) + ToolExecutor |
| `src/agents/research_agent.py` | Destination, flights, hotels, activities research |
| `src/agents/analysis_agent.py` | Feasibility, cost, schedule analysis |
| `src/agents/specialized_agents.py` | Budget, weather, safety, transport |
| `src/agents/itinerary_agent.py` | Itinerary generation |
| `src/utils/config.py` | Configuration management |
| `src/utils/prompts.py` | System prompts |

## Tool Dependencies & Parallel Execution

### Dependency Graph

Tools have data dependencies - some require results from others before they can run:

```
                           ┌─────────────────────────┐
                           │    research_destination │  ← MUST run first
                           │   (destination info)    │     (no dependencies)
                           └───────────┬─────────────┘
                                       │
              ┌────────────────────────┼────────────────────────┐
              │                        │                        │
              ▼                        ▼                        ▼
    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
    │ research_flights│    │research_hotels  │    │research_activity│  ← CAN run
    │   (flights)     │    │   (hotels)      │    │  (activities)   │    in PARALLEL
    └────────┬────────┘    └────────┬────────┘    └────────┬────────┘
             │                      │                      │
             └──────────────────────┼──────────────────────┘
                                    │
                                    ▼
    ┌───────────────────────────────────────────────────────────────┐
    │         analyze_feasibility, analyze_cost, analyze_weather,   │  ← CAN run
    │         analyze_safety, analyze_transport, optimize_budget    │    in PARALLEL
    └───────────────────────────────┬───────────────────────────────┘
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │  generate_itinerary   │  ← MUST run last
                        │  (final itinerary)    │    (needs all data)
                        └───────────────────────┘
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │   generate_summary    │  ← Optional
                        └───────────────────────┘
```

### Dependency Rules

| Tool | Depends On | Can Parallel With |
|------|------------|-------------------|
| `research_destination` | None | - |
| `research_flights` | destination | hotels, activities |
| `research_accommodations` | destination | flights, activities |
| `research_activities` | destination | flights, hotels |
| `analyze_itinerary_feasibility` | flights, hotels, activities | cost, weather, safety, transport |
| `analyze_cost_breakdown` | flights, hotels, activities | feasibility, weather, safety, transport |
| `analyze_weather` | destination, dates | feasibility, cost, safety, transport |
| `analyze_safety` | destination | feasibility, cost, weather, transport |
| `analyze_local_transport` | destination | feasibility, cost, weather, safety |
| `optimize_budget` | flights, hotels, activities | - |
| `generate_itinerary` | ALL research + analysis | - |
| `generate_summary` | itinerary | - |

### Why Iterations Exist

The LLM orchestrator makes decisions in **iterations** (rounds) because:

1. **Data Dependencies**: Can't analyze costs before knowing flight prices
2. **Context Building**: Each iteration adds information for better decisions
3. **Autonomous Decision-Making**: LLM decides what to call next based on results

```
Iteration 1: research_destination
   └── Need basic destination info before anything else

Iteration 2: research_flights + research_accommodations + research_activities
   └── These 3 tools have NO dependencies on each other → RUN IN PARALLEL
   └── All 3 need destination info from Iteration 1

Iteration 3: analyze_* tools (5 tools)
   └── All need research data from Iteration 2 → RUN IN PARALLEL
   └── No dependencies between analysis tools

Iteration 4: generate_itinerary
   └── Needs ALL previous data to create final plan
```

### Parallel Execution in Practice

When `ENABLE_PARALLEL_EXECUTION=true`:

```python
# Iteration 2 - 3 tools called together
if len(tool_calls) > 1 and enable_parallel:
    with ThreadPoolExecutor(max_workers=3) as executor:
        # All 3 start simultaneously
        futures = [
            executor.submit(research_flights, ...),
            executor.submit(research_accommodations, ...),
            executor.submit(research_activities, ...)
        ]
        # Wait for all to complete
        results = [f.result() for f in futures]
```

**Time savings example:**
- Sequential: 3 tools × 5 sec each = 15 seconds
- Parallel: 3 tools running together = ~5 seconds (3x faster)

### Iterations vs Parallel Execution

| Concept | Purpose | Example |
|---------|---------|---------|
| **Iterations** | LLM decision rounds - sequential by design | Iteration 1 → 2 → 3 |
| **Parallel Execution** | Multiple tools within ONE iteration | flights + hotels + activities |

The LLM cannot skip iterations because it needs results to make informed decisions.

## Performance Optimizations

1. **Flattened Architecture**: Single orchestrator loop instead of nested agents
2. **Parallel Tool Execution**: ThreadPoolExecutor for concurrent tools within iterations
3. **Lazy Agent Initialization**: Agents created only when first needed
4. **Result Caching**: Tools cache results to avoid duplicate Tavily API calls
5. **Minimal LLM Calls**: Deterministic sub-agents don't use LLM internally
6. **Smart Dependencies**: LLM groups independent tools for parallel execution
