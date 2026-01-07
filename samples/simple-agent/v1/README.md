# Naive Research Agent (v1)

A baseline research agent demonstrating the core agentic loop pattern. This is the first in a series of progressively improved agent architectures.

**Status:** ✅ Complete | **Complexity:** Beginner | **Version:** 1 of 4

## The Agent Evolution Series

This sample is part of a progressive demo series showing how to improve agent architecture:

| Version | Name | Focus | Key Improvement |
|---------|------|-------|-----------------|
| **v1** | **Naive Agent** (this) | Baseline | Single agent, sequential execution |
| v2 | Prompt Engineering | Better prompting | Query decomposition, chain-of-thought |
| v3 | Sub-Agent Architecture | Specialization | Planner, Searcher, Analyzer agents |
| v4 | Parallel Execution | Performance | Concurrent tool calls, parallel agents |

## What This Version Demonstrates

This naive implementation shows the **baseline approach**:

```
┌─────────────────────────────────────────────────────────────┐
│                    NAIVE AGENT (v1)                          │
│                                                              │
│   User Question                                              │
│        │                                                     │
│        ▼                                                     │
│   ┌─────────────────────────────────────────────────────┐   │
│   │            Single Agent                              │   │
│   │  (search + analyze + synthesize - ALL IN ONE)       │   │
│   └─────────────────────────────────────────────────────┘   │
│        │                                                     │
│        ▼                                                     │
│   Sequential Tool Calls:                                     │
│   search → wait → search → wait → answer                    │
│        │                                                     │
│        ▼                                                     │
│   Final Answer                                               │
└─────────────────────────────────────────────────────────────┘
```

### Intentional Limitations (to be improved in later versions)

1. **Single Agent**: One agent handles everything (no specialization)
2. **Sequential Execution**: Tool calls happen one at a time
3. **Basic Prompting**: Uses the question as-is (no decomposition)
4. **No Planning**: Jumps straight to searching
5. **Simple Synthesis**: Basic answer generation

## Quick Start

### 1. Setup

```bash
cd simple-agent
./setup.sh

# Or manually:
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### 2. Configure

Edit `.env`:

```bash
# LLM Gateway (for vLLora or other proxies)
LLM_BASE_URL=http://localhost:9090/v1

# OpenAI API Key (use dummy-key for local gateway)
OPENAI_API_KEY=dummy-key

# Tavily API Key (optional - uses mock if not set)
TAVILY_API_KEY=tvly-...
```

### 3. Run Demo

```bash
python examples/demo.py
```

### 4. Interactive Mode

```bash
python examples/interactive.py
```

## Available Tools

| Tool | Description |
|------|-------------|
| `web_search` | Search the web using Tavily API |
| `get_page_content` | Extract content from a webpage |
| `save_finding` | Save important research findings |

## Code Structure

```
simple-agent/
├── src/
│   ├── __init__.py      # Package exports
│   ├── agent.py         # NaiveResearchAgent with agentic loop
│   └── tools.py         # Tool definitions and implementations
├── examples/
│   ├── demo.py          # Guided demo with examples
│   └── interactive.py   # Chat with the agent
├── docs/
│   └── ARCHITECTURE.md  # Detailed architecture docs
├── requirements.txt
├── setup.sh
├── .env.example
└── README.md
```

## Example Usage

```python
from src import run_research

# Research a question
result = run_research(
    question="What are the latest developments in AI agents?",
    max_iterations=10,
    verbose=True
)

print(result.answer)
print(f"Sources: {result.sources}")
print(f"Tool calls: {len(result.tool_calls)}")
```

## The Agentic Loop

```python
while iteration < max_iterations:
    # 1. LLM decides what to do
    response = llm.create(messages=messages, tools=TOOLS)

    if response.tool_calls:
        # 2. Execute tools SEQUENTIALLY
        for tool_call in response.tool_calls:
            result = execute_tool(tool_call)
            messages.append(result)
    else:
        # 3. No more tools = done
        return response.content
```

## What's Next?

After understanding this baseline, explore the improved versions:

### v2: Prompt Engineering
- Query reformulation for better search
- Chain-of-thought reasoning
- Self-critique and verification

### v3: Sub-Agent Architecture
- **Planner Agent**: Breaks down complex questions
- **Searcher Agent**: Specialized in finding information
- **Analyzer Agent**: Extracts insights from content
- **Synthesizer Agent**: Combines findings into coherent answers

### v4: Parallel Execution
- Multiple searches running concurrently
- Parallel analysis of different sources
- Efficient coordination between agents

## Learn More

- [Architecture Documentation](./docs/ARCHITECTURE.md)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [Tavily Search API](https://tavily.com/)

## License

MIT
