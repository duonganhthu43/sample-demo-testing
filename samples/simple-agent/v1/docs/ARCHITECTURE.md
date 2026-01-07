# Naive Research Agent (v1) - Architecture

This document explains the architecture of the baseline research agent and highlights its intentional limitations that will be addressed in future versions.

## Overview

This is a **naive (baseline) implementation** designed to:
1. Demonstrate the core agentic loop pattern
2. Show fundamental function calling concepts
3. Highlight limitations that motivate improvements in v2, v3, v4

## The Agentic Loop

```
┌──────────────────────────────────────────────────────────────────┐
│                         USER QUESTION                             │
└──────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│                    SINGLE RESEARCH AGENT                          │
│         (does everything: search, analyze, synthesize)            │
└──────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌──────────────────────────────────────────────────────────────────┐
│              Send to LLM with tool definitions                    │
│              (tool_choice="auto")                                 │
└──────────────────────────────────────────────────────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Has tool_calls?    │
                    └─────────────────────┘
                      │                │
                     YES               NO
                      │                │
                      ▼                ▼
┌────────────────────────┐    ┌────────────────────────┐
│  Execute tools         │    │  Return final answer   │
│  SEQUENTIALLY          │    │        DONE            │
│  (one at a time)       │    │                        │
└────────────────────────┘    └────────────────────────┘
          │
          └──────────────────┐
                             │
                             ▼
                    (loop back to LLM)
```

## Intentional Limitations

### 1. Single Agent (No Specialization)

**Current (v1):**
```python
class NaiveResearchAgent:
    """One agent does everything"""

    def research(self, question):
        # Same agent: searches, analyzes, synthesizes
        pass
```

**Limitation:** No specialized expertise. The same agent handles everything from query planning to final synthesis.

**Future (v3):** Specialized sub-agents
```python
# Planner: breaks down complex questions
# Searcher: optimized for finding information
# Analyzer: extracts insights
# Synthesizer: creates coherent answers
```

### 2. Sequential Execution (No Parallelism)

**Current (v1):**
```python
# Tools execute one at a time
for tool_call in assistant_message.tool_calls:
    result = execute_tool(tool_call)  # Wait for each one
    messages.append(result)
```

**Limitation:** Slow! If we need 3 searches, we wait for each one sequentially.

**Future (v4):** Parallel execution
```python
with ThreadPoolExecutor() as executor:
    futures = [executor.submit(execute_tool, tc) for tc in tool_calls]
    results = [f.result() for f in as_completed(futures)]
```

### 3. Basic Prompting (No Query Decomposition)

**Current (v1):**
```python
SYSTEM_PROMPT = """You are a research assistant.
Search for information and provide an answer."""

# User question used as-is
messages.append({"role": "user", "content": question})
```

**Limitation:** Complex questions aren't broken down. The agent just starts searching with the raw query.

**Future (v2):** Query decomposition and chain-of-thought
```python
# Step 1: Analyze the question
# Step 2: Break into sub-questions
# Step 3: Reformulate for better search
# Step 4: Research each aspect
# Step 5: Synthesize with self-critique
```

### 4. No Planning Phase

**Current (v1):** Agent immediately starts calling tools without planning.

**Future (v3):** Explicit planning step
```python
plan = planner_agent.create_plan(question)
# Returns: [
#   "Search for X",
#   "Search for Y",
#   "Compare X and Y",
#   "Synthesize findings"
# ]
```

## Code Structure

### NaiveResearchAgent Class

```python
class NaiveResearchAgent:
    SYSTEM_PROMPT = """You are a research assistant..."""

    def __init__(self, model, max_iterations, verbose):
        self.client = OpenAI(...)

    def research(self, question: str) -> ResearchResult:
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": question}
        ]

        for iteration in range(max_iterations):
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=TOOL_DEFINITIONS,
                tool_choice="auto"
            )

            if response.tool_calls:
                # Execute SEQUENTIALLY
                for tool_call in response.tool_calls:
                    result = execute_tool(tool_call)
                    messages.append(result)
            else:
                # Done
                return ResearchResult(...)
```

### Tools

| Tool | Purpose |
|------|---------|
| `web_search` | Search web via Tavily API |
| `get_page_content` | Extract content from URL |
| `save_finding` | Save important findings |

### Data Flow

```
Question
    │
    ▼
┌─────────────────┐
│ NaiveResearch   │
│     Agent       │
└─────────────────┘
    │
    ▼
┌─────────────────┐     ┌─────────────────┐
│   OpenAI API    │────▶│    LLM Model    │
│                 │◀────│  (gpt-4o-mini)  │
└─────────────────┘     └─────────────────┘
    │
    │ tool_calls (SEQUENTIAL)
    ▼
┌─────────────────┐
│  execute_tool   │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│  web_search     │────▶ Tavily API
│  get_page_cont  │────▶ Tavily Extract
│  save_finding   │────▶ In-memory store
└─────────────────┘
    │
    │ results (one at a time)
    ▼
(back to LLM for next decision)
```

## Comparison: v1 vs Future Versions

| Aspect | v1 (Naive) | v2 (Prompting) | v3 (Sub-Agents) | v4 (Parallel) |
|--------|------------|----------------|-----------------|---------------|
| Agents | 1 | 1 | 4+ | 4+ |
| Execution | Sequential | Sequential | Sequential | Parallel |
| Query handling | As-is | Decomposed | Planned | Planned |
| Prompting | Basic | Chain-of-thought | Role-specific | Role-specific |
| Planning | None | Implicit | Explicit | Explicit |
| Speed | Slow | Slow | Medium | Fast |

## Why Start Here?

This naive implementation is valuable because:

1. **Simplicity**: Easy to understand the core pattern
2. **Foundation**: Shows what we're building upon
3. **Motivation**: Makes limitations visible, motivating improvements
4. **Debugging**: Simple code is easier to debug
5. **Baseline**: Provides a comparison point for measuring improvements

## Running the Agent

```python
from src import run_research

result = run_research(
    question="What are the latest developments in AI agents?",
    max_iterations=10,
    verbose=True
)

print(result.answer)
print(f"Tool calls: {len(result.tool_calls)}")
print(f"Duration: {result.total_duration:.2f}s")
```

## Next Steps

After understanding this baseline:

1. **v2: Prompt Engineering** - Better prompting without architectural changes
2. **v3: Sub-Agent Architecture** - Specialized agents for different tasks
3. **v4: Parallel Execution** - Concurrent processing for performance

Each version builds on the previous, showing incremental improvements.
