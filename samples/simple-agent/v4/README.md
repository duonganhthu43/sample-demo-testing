# Simple Agent v4 - Parallel Execution

This version adds **parallel execution** to maximize performance.
Same sub-agent architecture as v3, but with concurrent tool execution.

## What's Different from v3?

| Aspect | v3 (Sub-Agents) | v4 (Parallel) |
|--------|-----------------|---------------|
| Search execution | Sequential | Parallel |
| Content extraction | One at a time | Concurrent |
| Performance | Baseline | 2-4x faster |
| Architecture | Same | Same |

## Parallel Execution Details

### ThreadPoolExecutor
v4 uses Python's `concurrent.futures.ThreadPoolExecutor` for parallel execution:

```python
with ThreadPoolExecutor(max_workers=4) as executor:
    # Submit all searches at once
    futures = {executor.submit(web_search, q): q for q in queries}

    # Collect results as they complete
    for future in as_completed(futures):
        result = future.result()
```

### What Runs in Parallel

1. **Search Phase**: All search queries execute concurrently
   - v3: Query 1 → Query 2 → Query 3 (sequential)
   - v4: Query 1, Query 2, Query 3 (parallel)

2. **Extraction Phase**: Multiple URLs fetched concurrently
   - v3: URL 1 → URL 2 → URL 3 (sequential)
   - v4: URL 1, URL 2, URL 3 (parallel)

### What Remains Sequential

- Planning (single LLM call)
- Analysis (needs all search results)
- Synthesis (needs analysis complete)

## Performance Metrics

v4 tracks performance improvements:

```
--- Performance (v4) ---
Parallel searches: 4
Actual duration: 3.2s
Est. sequential time: 8.5s
Estimated speedup: 2.7x
```

## Quick Start

```bash
# Navigate to simple-agent directory
cd samples/simple-agent

# Create .env if not already done (shared by all versions)
cp .env.example .env
# Edit .env with your settings

# Activate shared virtual environment
source venv/bin/activate

# Run v4 demo
cd v4
python examples/demo.py
```

## Configuration

Same as v1/v2/v3 - uses `LLM_BASE_URL`, `OPENAI_API_KEY`, `OPENAI_MODEL`, and `TAVILY_API_KEY`.

Additional v4 parameter:
- `max_workers`: Number of parallel workers (default: 4)

## Comparing v3 vs v4

Run both demos and compare execution time:

```bash
# Terminal 1: Run v3 (sequential)
cd samples/simple-agent/v3
time python examples/demo.py

# Terminal 2: Run v4 (parallel)
cd samples/simple-agent/v4
time python examples/demo.py
```

Observe:
- v4 completes faster with same quality
- Multiple searches happening simultaneously
- Performance metrics in output

## Workflow

```
Question
    │
    ▼
┌─────────────┐
│   Planner   │ → Research plan + search queries
└─────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│         PARALLEL SEARCH             │
│  ┌───┐  ┌───┐  ┌───┐  ┌───┐       │
│  │ Q1│  │ Q2│  │ Q3│  │ Q4│       │
│  └───┘  └───┘  └───┘  └───┘       │
│     ↓      ↓      ↓      ↓         │
│  [Results aggregated]              │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────────────────────────────┐
│      PARALLEL EXTRACTION            │
│  ┌────┐  ┌────┐  ┌────┐            │
│  │URL1│  │URL2│  │URL3│            │
│  └────┘  └────┘  └────┘            │
└─────────────────────────────────────┘
    │
    ▼
┌─────────────┐
│  Analyzer   │ → Insights
└─────────────┘
    │
    ▼
┌─────────────┐
│ Synthesizer │ → Final answer
└─────────────┘
```

## The Complete Progression

| Version | Focus | Key Improvement |
|---------|-------|-----------------|
| v1 | Baseline | Basic agentic loop |
| v2 | Quality | Better prompting |
| v3 | Organization | Specialized sub-agents |
| v4 | Performance | Parallel execution |

Each version builds on the previous, demonstrating one architectural improvement at a time.
