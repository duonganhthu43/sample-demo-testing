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
    # ... 15 more tools (16 total)
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

### Two Separate Data Flows (Important!)

There are **two separate data flows** in the architecture:

```
┌─────────────────────────────────────────────────────────────────────────┐
│  1. ORCHESTRATOR MESSAGES (for decision-making)                         │
│     └── Conversation history with tool results (can be compressed)      │
│     └── Only needs summaries: "Found 8 flights $180-$450"               │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│  2. TOOL EXECUTOR CONTEXT (for specialized agents)                      │
│     └── Full data stored in self.context dictionary                     │
│     └── Agents access via tool_executor.get_context()                   │
│     └── Contains ALL details: prices, amenities, images, etc.           │
└─────────────────────────────────────────────────────────────────────────┘
```

**Key insight**: Specialized agents (itinerary_agent, presentation_agent, etc.) get their data from `tool_executor.context`, **NOT** from the orchestrator's conversation messages!

```python
# In tools.py - Results stored in context with FULL data
self.context["research"].append({"type": "flights", **result.to_dict()})

# In itinerary_agent.py - Gets FULL data from context
context = tool_executor.get_context()  # Contains complete flight/hotel/activity data
flights = context["research"][1]        # Full flight data with all details
```

**Why this matters for optimization**:
- The orchestrator's messages can be **compressed/summarized** without losing data
- Specialized agents always access **full data** from `tool_executor.context`
- Compressing orchestrator messages reduces token usage by ~80% without affecting quality

| Data Flow | Purpose | Can Compress? |
|-----------|---------|---------------|
| Orchestrator messages | Decide which tool to call next | ✅ Yes - only needs summaries |
| Tool executor context | Full data for specialized agents | ❌ No - needs all details |

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

3. Agentic Loop (typical execution)
   │
   ├─ Iteration 1: research_destination
   │   └─ Result: destination info, visa, culture tips
   │
   ├─ Iteration 2: research_flights + research_accommodations +
   │               research_activities + research_restaurants (PARALLEL)
   │   └─ Results: flights, hotels, activities, restaurants with images
   │
   ├─ Iteration 3: analyze_* tools (PARALLEL)
   │   └─ Results: feasibility, cost, schedule, weather, safety, transport
   │
   ├─ Iteration 4: generate_itinerary
   │   └─ Result: day-by-day itinerary with image_suggestion fields
   │
   ├─ Iteration 5: fetch_images
   │   └─ Result: targeted images for itinerary items (via ImageAgent)
   │
   ├─ Iteration 6: format_presentation
   │   └─ Result: beautiful markdown with embedded images
   │
   └─ Iteration 7+: LLM stops (no more tool calls) or generate_summary

4. Result Assembly
   │
   └─ TravelPlanResult with itinerary, presentation, costs, all context
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
    agent: AgentConfig    # Max iterations, request timeout
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

### Core Orchestration
| File | Purpose |
|------|---------|
| `src/agents/agentic_orchestrator.py` | Main LLM orchestrator with function calling loop |
| `src/agents/tools.py` | Tool definitions (16 tools) + ToolExecutor |

### Research Agents
| File | Purpose |
|------|---------|
| `src/agents/research_agent.py` | Destination research via Tavily + LLM extraction |
| `src/agents/flight_search_agent.py` | LLM-powered flight search with Tavily |
| `src/agents/hotel_search_agent.py` | LLM-powered hotel search with Tavily |
| `src/agents/activity_search_agent.py` | LLM-powered activity/attraction search |
| `src/agents/restaurant_search_agent.py` | LLM-powered restaurant search |

### Analysis & Specialized Agents
| File | Purpose |
|------|---------|
| `src/agents/analysis_agent.py` | Feasibility, cost, schedule analysis |
| `src/agents/specialized_agents.py` | Budget, weather, safety, transport analysis |

### Output Generation
| File | Purpose |
|------|---------|
| `src/agents/itinerary_agent.py` | Day-by-day itinerary generation |
| `src/agents/image_agent.py` | Targeted image fetching based on itinerary content |
| `src/agents/presentation_agent.py` | Markdown formatting with image embedding |

### Tools & Utilities
| File | Purpose |
|------|---------|
| `src/tools/image_search.py` | ImageSearchTool using Tavily API for image discovery |
| `src/tools/image_utils.py` | Image download, base64 encoding, caching, deduplication |
| `src/tools/weather_service.py` | Weather data fetching |
| `src/utils/config.py` | Configuration management |
| `src/utils/prompts.py` | System prompts |
| `src/utils/schemas.py` | JSON schemas for structured outputs (10 schemas) |

## Tool Dependencies & Parallel Execution

### Dependency Graph

Tools have data dependencies - some require results from others before they can run:

```
                           ┌─────────────────────────┐
                           │    research_destination │  ← MUST run first
                           │   (destination info)    │     (no dependencies)
                           └───────────┬─────────────┘
                                       │
     ┌─────────────────┬───────────────┼───────────────┬─────────────────┐
     │                 │               │               │                 │
     ▼                 ▼               ▼               ▼                 ▼
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ research │    │ research │    │ research │    │ research │    │   CAN    │
│ _flights │    │ _hotels  │    │_activity │    │_restaurants   │   run    │
└────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘    │ PARALLEL │
     │               │               │               │          └──────────┘
     └───────────────┴───────────────┴───────────────┘
                                    │
                                    ▼
    ┌───────────────────────────────────────────────────────────────┐
    │  analyze_feasibility, analyze_cost, analyze_schedule,         │  ← CAN run
    │  analyze_weather, analyze_safety, analyze_transport,          │    in PARALLEL
    │  optimize_budget                                              │
    └───────────────────────────────┬───────────────────────────────┘
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │  generate_itinerary   │  ← MUST run
                        │  (final itinerary)    │    (needs all data)
                        └───────────┬───────────┘
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │    fetch_images       │  ← Fetches targeted
                        │  (ImageAgent)         │    images for itinerary
                        └───────────┬───────────┘
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │  format_presentation  │  ← FINAL step
                        │  (markdown + images)  │    (embeds images)
                        └───────────────────────┘
```

### Dependency Rules

| Tool | Depends On | Can Parallel With |
|------|------------|-------------------|
| `research_destination` | None | - |
| `research_flights` | destination | hotels, activities, restaurants |
| `research_accommodations` | destination | flights, activities, restaurants |
| `research_activities` | destination | flights, hotels, restaurants |
| `research_restaurants` | destination | flights, hotels, activities |
| `analyze_itinerary_feasibility` | flights, hotels, activities | cost, schedule, weather, safety, transport |
| `analyze_cost_breakdown` | flights, hotels, activities | feasibility, schedule, weather, safety, transport |
| `analyze_schedule_optimization` | flights, hotels, activities | feasibility, cost, weather, safety, transport |
| `analyze_weather` | destination, dates | feasibility, cost, schedule, safety, transport |
| `analyze_safety` | destination | feasibility, cost, schedule, weather, transport |
| `analyze_local_transport` | destination | feasibility, cost, schedule, weather, safety |
| `optimize_budget` | flights, hotels, activities | - |
| `generate_itinerary` | ALL research + analysis | - |
| `fetch_images` | itinerary | - |
| `generate_summary` | itinerary | - |
| `format_presentation` | itinerary, images | - |

### Why Iterations Exist

The LLM orchestrator makes decisions in **iterations** (rounds) because:

1. **Data Dependencies**: Can't analyze costs before knowing flight prices
2. **Context Building**: Each iteration adds information for better decisions
3. **Autonomous Decision-Making**: LLM decides what to call next based on results

```
Iteration 1: research_destination
   └── Need basic destination info before anything else

Iteration 2: research_flights + research_accommodations + research_activities + research_restaurants
   └── These 4 tools have NO dependencies on each other → RUN IN PARALLEL
   └── All 4 need destination info from Iteration 1

Iteration 3: analyze_* tools (7 tools)
   └── All need research data from Iteration 2 → RUN IN PARALLEL
   └── No dependencies between analysis tools

Iteration 4: generate_itinerary
   └── Needs ALL previous data to create final plan

Iteration 5: fetch_images
   └── ImageAgent fetches targeted images based on itinerary content
   └── Uses Tavily API with advanced search for diverse, unique images

Iteration 6: format_presentation
   └── Creates beautiful markdown output with embedded images
   └── Uses 7-strategy fuzzy matching for placeholder-to-image mapping
```

### Parallel Execution

Multiple tools within an iteration are always executed in parallel using `ThreadPoolExecutor`:

```python
# Multiple tools called together in one iteration
with ThreadPoolExecutor(max_workers=len(tool_calls)) as executor:
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
5. **LLM-Powered Agents**: Most agents use LLM for intelligent processing
6. **Smart Dependencies**: LLM groups independent tools for parallel execution
7. **Context Compression Ready**: Orchestrator messages can be compressed without losing data (see "Two Separate Data Flows" section)

### Potential Optimization: Orchestrator Context Compression

Based on trace analysis, the orchestrator's input tokens grow from ~1,600 to ~22,000+ across iterations. Since specialized agents get full data from `tool_executor.context`, the orchestrator's messages can be safely compressed:

```python
# Before (full result ~5KB):
messages.append({"role": "tool", "content": json.dumps(full_result)})

# After (summary ~200 bytes):
messages.append({"role": "tool", "content": "Found 8 flights ($180-$450), 3 direct"})
```

**Expected impact**: ~80% reduction in orchestrator token usage, ~30-40% faster orchestrator response times.

## LLM Usage by Agent

| Agent | Uses LLM | Purpose |
|-------|----------|---------|
| `AgenticOrchestrator` | ✅ Yes | Main decision-making loop with function calling |
| `ResearchAgent` | ✅ Yes | Destination research via Tavily + LLM extraction |
| `FlightSearchAgent` | ✅ Yes | Flight search via Tavily + LLM structuring |
| `HotelSearchAgent` | ✅ Yes | Hotel search via Tavily + LLM structuring |
| `ActivitySearchAgent` | ✅ Yes | Activity search via Tavily + LLM structuring |
| `RestaurantSearchAgent` | ✅ Yes | Restaurant search via Tavily + LLM structuring |
| `AnalysisAgent` | ✅ Yes | Intelligent feasibility, cost, schedule analysis |
| `SpecializedAgents` | ✅ Yes | Tavily API + LLM for budget, weather, safety, transport |
| `ItineraryAgent` | ✅ Yes | Generates intelligent day-by-day schedules |
| `ImageAgent` | ❌ No | Uses Tavily API directly for image search |
| `PresentationAgent` | ✅ Yes | Formats output as professional markdown |

### ResearchAgent
Uses Tavily API to search for destination information, then LLM to extract structured data:
- Visa requirements, language, currency, timezone
- Cultural tips and local cuisine
- Safety ratings and best time to visit

### Specialized Search Agents
Each search agent follows a similar pattern: Tavily search → LLM extraction with structured outputs:

| Agent | Tavily Queries | LLM Schema | Output |
|-------|---------------|------------|--------|
| `FlightSearchAgent` | Flight schedules, prices | `FLIGHT_SEARCH_SCHEMA` | Flight options with airlines, times, prices |
| `HotelSearchAgent` | Hotels, accommodations | `HOTEL_SEARCH_SCHEMA` | Hotels with ratings, amenities, prices |
| `ActivitySearchAgent` | Attractions, activities | `ACTIVITY_SEARCH_SCHEMA` | Activities with categories, durations, tips |
| `RestaurantSearchAgent` | Restaurants, dining | `RESTAURANT_SEARCH_SCHEMA` | Restaurants with cuisine, price ranges |

**Features:**
- Parallel Tavily searches for comprehensive coverage
- LLM-powered data extraction with JSON schema validation
- Automatic image downloading for visual content
- Caching to avoid duplicate API calls

### AnalysisAgent
Uses LLM for intelligent analysis:
- **Feasibility Analysis**: Evaluates if itinerary is realistic based on time, logistics, budget
- **Cost Breakdown**: Calculates costs with destination-specific estimates for food/transport
- **Schedule Optimization**: Groups activities by location, optimizes travel time

### SpecializedAgents
All specialized agents use Tavily API for real-time data + LLM for intelligent extraction:

- **BudgetAgent**: Analyzes costs and provides destination-specific optimization recommendations
- **WeatherAgent**: Generates intelligent weather advisories and packing suggestions
- **SafetyAgent**: Extracts safety tips, emergency contacts, scam warnings, health advisories
- **TransportAgent**: Analyzes local transport options, tourist passes, airport transfers

### ItineraryAgent
Uses LLM to generate intelligent itineraries with:
- Realistic time schedules based on activity durations
- Appropriate meal times for the destination
- Cost estimates based on destination cost level
- Context-aware packing lists and notes

### PresentationAgent
Uses LLM to generate beautiful, context-aware markdown formatting with tables, checklists, and links.

## Structured Outputs (JSON Schema)

The agent uses OpenAI's **Structured Outputs** feature to ensure LLM responses are always valid, schema-compliant JSON. This eliminates parsing errors and provides type-safe responses.

### Schema Definitions

Located in `src/utils/schemas.py`:

```python
# Helper function to create response_format dict
def get_response_format(schema_name: str, schema: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "type": "json_schema",
        "json_schema": {
            "name": schema_name,
            "schema": schema,
            "strict": True  # Enforces exact schema compliance
        }
    }
```

### Available Schemas

| Schema | Used By | Purpose |
|--------|---------|---------|
| `ITINERARY_SCHEMA` | ItineraryAgent | Day-by-day itinerary with schedule, costs, packing list |
| `DESTINATION_EXTRACTION_SCHEMA` | ResearchAgent | Visa, language, currency, cultural tips, safety info |
| `WEATHER_FORECAST_SCHEMA` | WeatherService | Daily forecasts, averages, packing suggestions |
| `FLIGHT_SEARCH_SCHEMA` | FlightSearchAgent | Flight options with prices, airlines, schedules |
| `HOTEL_SEARCH_SCHEMA` | HotelSearchAgent | Hotel options with ratings, amenities, locations |
| `ACTIVITY_SEARCH_SCHEMA` | ActivitySearchAgent | Activities/attractions with categories, prices, tips |
| `RESTAURANT_SEARCH_SCHEMA` | RestaurantSearchAgent | Restaurants with cuisine, price ranges, specialties |
| `FEASIBILITY_ANALYSIS_SCHEMA` | AnalysisAgent | Feasibility scores, concerns, recommendations |
| `COST_BREAKDOWN_SCHEMA` | AnalysisAgent | Itemized costs, daily averages, budget status |
| `SCHEDULE_OPTIMIZATION_SCHEMA` | AnalysisAgent | Optimized schedule with conflict detection |

### Schema Requirements for Strict Mode

OpenAI's strict mode requires:
1. **All properties in `required` array** - Every property defined must be listed as required
2. **`additionalProperties: false`** - No extra fields allowed beyond schema definition
3. **Explicit types** - All fields must have explicit type definitions

Example from `ITINERARY_SCHEMA`:
```python
{
    "type": "object",
    "properties": {
        "days": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "day": {"type": "integer"},
                    "date": {"type": "string"},
                    "theme": {"type": "string"},
                    "schedule": {...},
                    "day_cost": {"type": "number"}
                },
                "required": ["day", "date", "theme", "schedule", "day_cost"],
                "additionalProperties": False
            }
        },
        "total_estimated_cost": {"type": "number"},
        "summary": {"type": "string"},
        "packing_list": {"type": "array", "items": {"type": "string"}},
        "important_notes": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["days", "total_estimated_cost", "summary", "packing_list", "important_notes"],
    "additionalProperties": False
}
```

### Fallback Handling

For LLM providers that don't support `response_format` with JSON schema, agents gracefully fall back:

```python
try:
    response = client.chat.completions.create(
        model=self.config.llm.model,
        messages=messages,
        response_format=get_response_format("itinerary", ITINERARY_SCHEMA),
        ...
    )
except Exception as e:
    msg = str(e).lower()
    if "response_format" in msg or "unknown" in msg or "unsupported" in msg:
        # Fallback: retry without response_format
        response = client.chat.completions.create(
            model=self.config.llm.model,
            messages=messages,
            ...
        )
```

### Benefits

1. **Guaranteed Valid JSON**: No parsing errors or malformed responses
2. **Type Safety**: Fields always have expected types (string, number, array, etc.)
3. **Consistent Structure**: Every response follows the exact same shape
4. **Better Error Messages**: Schema violations are caught by the API, not in application code

## Image Handling Architecture

### Overview

The travel planning agent uses a multi-stage image pipeline:
1. **ImageAgent** - Fetches targeted images based on itinerary content
2. **PresentationAgent** - Embeds images using placeholder matching

### Why Images Don't Appear in Traces

The presentation agent embeds images into the final markdown output, but **images are NOT visible in the LLM traces**. This is **by design** for efficiency reasons.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│  WHY IMAGES ARE NOT IN TRACES                                                 │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. LLM CALL (traced in vLLora)                                              │
│     ├── Input: context data + image registry (base64 data)                   │
│     ├── Output: markdown with IMAGE_PLACEHOLDER:xxx patterns                 │
│     └── Why? Base64 images are HUGE (50KB+ each). Generating them            │
│             directly would waste tokens and slow down the LLM.               │
│                                                                              │
│  2. POST-PROCESSING (NOT traced - happens after LLM call)                    │
│     ├── Input: markdown with placeholders + image registry                   │
│     ├── Process: _replace_image_placeholders() matches & substitutes         │
│     └── Output: final markdown with embedded base64 images                   │
│                                                                              │
│  Result: Traces show placeholders, saved files show actual images            │
└──────────────────────────────────────────────────────────────────────────────┘
```

### The Placeholder Pattern

Instead of asking the LLM to generate base64 data (impossible) or copy it from input (wasteful), we use a **placeholder pattern**:

```python
# LLM generates this in markdown:
"![Tokyo Skyline](IMAGE_PLACEHOLDER:tokyo_skyline)"
"![Sensoji Temple](IMAGE_PLACEHOLDER:sensoji_temple)"

# Post-processing replaces with actual base64:
"![Tokyo Skyline](data:image/jpeg;base64,/9j/4AAQSkZJRg...)"
```

### Image Registry Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  COMPLETE IMAGE FLOW                                                         │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Step 1: Research Collection (during research tools)                        │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │ HotelSearchAgent, ActivitySearchAgent, RestaurantSearchAgent       │     │
│  │ Each downloads images via Tavily API for found items               │     │
│  │ Images stored with items: {"name": "...", "images": ["base64..."]} │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                               │                                             │
│                               ▼                                             │
│  Step 2: Itinerary Generation                                               │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │ ItineraryAgent creates day-by-day plan with image_suggestion keys  │     │
│  │ e.g., {"activity": "Visit Sensoji", "image_suggestion": "sensoji"} │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                               │                                             │
│                               ▼                                             │
│  Step 3: Targeted Image Fetching (ImageAgent via fetch_images tool)         │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │ ImageAgent analyzes itinerary to extract image requirements        │     │
│  │ Fetches targeted images via Tavily API (advanced search, 5 results)│     │
│  │ Deduplicates images using URL-based tracking (before downloading)  │     │
│  │ Returns: {"sensoji_temple": "base64...", "hero": "base64..."...}   │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                               │                                             │
│                               ▼                                             │
│  Step 4: Registry Building (in PresentationAgent)                           │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │ Combines images from: ImageAgent results + research context        │     │
│  │ Normalizes keys using normalize_image_key() for consistent matching│     │
│  │ Creates stripped lookup table (no underscores) for fuzzy matching  │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                               │                                             │
│                               ▼                                             │
│  Step 5: LLM Generation (TRACED in vLLora)                                  │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │ LLM receives: registry keys as available_images list               │     │
│  │ LLM generates: markdown with IMAGE_PLACEHOLDER:xxx patterns        │     │
│  │ Traces show: "IMAGE_PLACEHOLDER:sensoji_temple" (not base64!)      │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                               │                                             │
│                               ▼                                             │
│  Step 6: Post-Processing (NOT traced - Python code after LLM)               │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │ _replace_image_placeholders() finds all IMAGE_PLACEHOLDER:xxx      │     │
│  │ 7-strategy fuzzy matching (see table below)                        │     │
│  │ Replaces with: data:image/jpeg;base64,/9j/4AAQ...                  │     │
│  │ Falls back to category-based images or SVG placeholders            │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                               │                                             │
│                               ▼                                             │
│  Step 7: Final Output (saved to file)                                       │
│  ┌────────────────────────────────────────────────────────────────────┐     │
│  │ outputs/travel_plan_{thread_id}.md contains embedded images        │     │
│  │ Can be opened in any markdown viewer to see actual images          │     │
│  └────────────────────────────────────────────────────────────────────┘     │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Fuzzy Matching Strategies

The placeholder-to-image matching uses 7 strategies (in order of priority):

| Strategy | Example Match | Priority |
|----------|---------------|----------|
| Exact match | `sensoji_temple` → `sensoji_temple` | 1 (highest) |
| Normalized match | `Sensoji Temple` → `sensoji_temple` | 2 |
| Stripped match | `sensojitemple` → `sensoji_temple` (underscores removed) | 3 |
| Contains match | `visitsensojitemple` → `sensoji_temple` | 3b |
| Partial match | `sensoji` found in `sensoji_temple_tokyo` | 4 |
| Word overlap scoring | `tokyo_temple` matches `sensoji_temple` (1+ word overlap) | 5 |
| Single-word fallback | `temple` → first key containing "temple" | 6 |
| Category fallback | Unmatched "restaurant" → any available restaurant image | 7 (lowest) |

**Key Normalization:**
```python
# normalize_image_key() in image_utils.py
"Sensoji Temple" → "sensoji_temple"
"Ichiran Ramen (Shibuya)" → "ichiran_ramen_shibuya"
```

**Image Deduplication:**
- Uses URL-based tracking at ImageSearchTool level
- Checks URL before downloading (more efficient)
- `_search_tavily()` returns list of URLs for fallback options
- Prevents same image from appearing for different items

### Why This Design?

1. **Token Efficiency**: Base64 images are 50KB+ each. Embedding 10 images would add 500KB+ to LLM input/output, massively increasing costs and latency.

2. **Clean Traces**: vLLora traces show the actual LLM reasoning, not bloated base64 strings.

3. **Flexible Matching**: LLM can use semantic names (`sensoji_temple`) without knowing exact registry keys.

4. **Separation of Concerns**: LLM focuses on content creation; Python handles data embedding.

### ImageAgent Details

The `ImageAgent` (in `src/agents/image_agent.py`) analyzes the generated itinerary to fetch targeted images:

```python
class ImageAgent:
    def fetch_images_for_itinerary(self, itinerary, context, max_images=15):
        # 1. Extract image queries from itinerary
        queries = self._extract_image_queries(itinerary, context, destination)

        # 2. Prioritize by category (attractions > hotels > restaurants)
        prioritized = self._prioritize_queries(queries, max_images)

        # 3. Fetch hero image first
        hero = self.image_search.search_hero_image(destination)

        # 4. Fetch remaining images in parallel
        results = self.image_search.search_multiple(prioritized, destination)

        return ImageFetchResult(images=results, ...)
```

**Query Extraction Sources:**
- Schedule items with `image_suggestion` field
- Activity names (for landmarks)
- Hotel names from accommodations research
- Restaurant names from dining research

**Tavily API Configuration:**
- `max_results=5` - More candidates per query
- `search_depth="advanced"` - More thorough search
- `include_images=True` - Direct image URL extraction

### Debugging Image Issues

If images are missing in the final output:

1. **Check ImageAgent logs**: Look for "Searching images for N items in parallel..."
2. **Check URL deduplication**: "Skipping duplicate URL" messages indicate same URL being returned
3. **Check registry keys**: Presentation agent logs show "Image placeholders: X/Y matched"
4. **Check unmatched**: Logs show "Unmatched placeholders: [keys]" and stripped versions
5. **Add retry logic**: `simplify_query()` in image_utils.py creates fallback search queries
