# Simple Agent - Progressive Demo Series

A progressive demonstration of agent architectures, starting from a naive implementation and improving step-by-step.

## Version Overview

| Version | Focus | Architecture | Key Feature |
|---------|-------|--------------|-------------|
| **v1** | Baseline | Single agent, sequential | Basic agentic loop |
| **v2** | Prompting | Single agent, sequential | Query decomposition, chain-of-thought |
| **v3** | Specialization | Multi-agent, sequential | Sub-agents (planner, searcher, analyzer) |
| **v4** | Performance | Multi-agent, parallel | Concurrent tool execution |
| **v5** | Debug Testing | Single agent, buggy | Intentional semantic errors for tracing |

## Analysis Demos (NEW!)

Focused demos for showcasing Lucy's analysis capabilities:

| Demo | Focus | User Question | Key Output |
|------|-------|---------------|------------|
| **demos/error-detection** | Tool errors | "What's wrong?" | Error table with severity |
| **demos/cost-analysis** | Cost breakdown | "Why expensive?" | Cost by model table |
| **demos/latency-analysis** | Performance | "Analyze performance" | Latency percentiles (p50/p95/p99) |
| **demos/semantic-analysis** | Prompt issues | "Is anything wrong?" | Contradictory instructions |
| **demos/hidden-issues** | Lucy vs Human | "Is anything wrong?" | 5+ hidden issues humans miss |

See [demos/README.md](demos/README.md) for full documentation.

## Quick Start

```bash
# Setup (one-time)
cd samples/simple-agent
python -m venv venv
source venv/bin/activate
pip install -r v1/requirements.txt

# Create .env (shared by all versions)
cp .env.example .env
# Edit .env with your settings
```

## Running the Demos

### v1 - Naive Agent (Baseline)
```bash
cd v1
python examples/demo.py
```
A single agent doing everything: search, analyze, answer.

### v2 - Improved Prompting
```bash
cd v2
python examples/demo.py
```
Same architecture as v1, but with better prompts for:
- Query decomposition
- Chain-of-thought reasoning
- Optimized search queries

### v3 - Sub-Agent Architecture
```bash
cd v3
python examples/demo.py
```
Specialized agents working together:
- Planner Agent: Creates research strategy
- Searcher Agent: Executes searches
- Analyzer Agent: Extracts insights
- Synthesizer Agent: Combines findings

### v4 - Parallel Execution
```bash
cd v4
python examples/demo.py
```
Performance optimization with:
- Concurrent search execution (ThreadPoolExecutor)
- Parallel content extraction
- Performance metrics and speedup tracking

### v5 - Debug Testing (Intentionally Buggy)
```bash
cd v5
python examples/demo.py
```
**WARNING: Contains intentional bugs for testing debug tracing agents!**

Bugs included:
- Tool name mismatch (schema vs executor)
- Conflicting system prompt instructions
- Missing parameters in tool schema
- Response format mismatch
- Poor error handling

Use this to test if your debug tracing agent can identify issues from LLM traces.

## Configuration

All versions use the same environment variables:

```bash
# LLM Gateway URL (for vLLora or other proxies)
LLM_BASE_URL=http://localhost:9090/v1

# OpenAI API Key
OPENAI_API_KEY=your-key-here

# Model to use
OPENAI_MODEL=gpt-4o-mini

# Tavily API Key for web search (optional - uses mock data if not set)
TAVILY_API_KEY=tvly-your-key-here
```

## Observability

All versions send these headers for tracing:
- `x-thread-id`: Unique conversation ID
- `x-run-id`: Unique execution ID
- `x-label`: Agent version identifier

## Directory Structure

```
simple-agent/
├── README.md          # This file
├── .env.example       # Environment config template
├── .env               # Your local config (shared by all versions)
├── venv/              # Shared virtual environment
├── demos/             # Analysis demos for Lucy
│   ├── error-detection/   # Tool error demo
│   ├── cost-analysis/     # Multi-model cost demo
│   ├── latency-analysis/  # Performance bottleneck demo
│   ├── semantic-analysis/ # Contradictory prompt demo
│   └── hidden-issues/     # Lucy vs Human challenge
├── v1/                # Naive baseline agent
│   ├── src/
│   │   ├── agent.py   # NaiveResearchAgent
│   │   └── tools.py   # Tool definitions
│   ├── examples/
│   │   └── demo.py    # Demo script
│   └── README.md
├── v2/                # Improved prompting
│   ├── src/
│   │   ├── agent.py   # ResearchAgentV2
│   │   └── tools.py   # Same tools
│   ├── examples/
│   │   └── demo.py    # Demo script
│   └── README.md
├── v3/                # Sub-agent architecture
│   ├── src/
│   │   ├── agent.py   # ResearchAgentV3 with sub-agents
│   │   └── tools.py   # Same tools
│   ├── examples/
│   │   └── demo.py    # Demo script
│   └── README.md
├── v4/                # Parallel execution
│   ├── src/
│   │   ├── agent.py   # ResearchAgentV4 with parallel execution
│   │   └── tools.py   # Same tools
│   ├── examples/
│   │   └── demo.py    # Demo script
│   └── README.md
└── v5/                # Debug testing (BUGGY!)
    ├── src/
    │   ├── agent.py   # ResearchAgentV5 with intentional bugs
    │   └── tools.py   # Tools with semantic errors
    ├── examples/
    │   └── demo.py    # Demo script
    └── README.md
```

## Learning Objectives

By running through these versions, you'll understand:

1. **v1 → v2**: How prompting alone can significantly improve agent behavior
2. **v2 → v3**: How specialization enables better task handling
3. **v3 → v4**: How parallelization improves performance
4. **v5 (standalone)**: How to identify semantic errors through LLM trace analysis

v1-v4 build progressively. v5 is a separate "buggy" version for testing debug tools.
