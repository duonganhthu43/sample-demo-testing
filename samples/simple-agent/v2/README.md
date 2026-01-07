# Simple Agent v2 - Improved Prompting

This version improves on v1 through **better prompting techniques** only.
The architecture remains the same (single agent, sequential execution).

## What's Different from v1?

| Aspect | v1 (Naive) | v2 (Improved Prompting) |
|--------|------------|-------------------------|
| System Prompt | Basic instructions | Detailed methodology |
| Query Handling | Direct search | Query decomposition |
| Reasoning | Implicit | Chain-of-thought |
| Search Queries | Full questions | Optimized keywords |
| Synthesis | Simple | Structured approach |

## Key Prompting Techniques

### 1. Query Decomposition
Before searching, the agent breaks complex questions into sub-questions:
```
Original: "What are AI agents and how do they work?"
Sub-questions:
- What is the definition of an AI agent?
- What components make up an AI agent?
- How do AI agents make decisions?
```

### 2. Chain-of-Thought Reasoning
The agent explicitly states its thinking before each action:
```
"I need to understand the core components of AI agents first.
I'll search for 'AI agent architecture components' to find
technical details about how they're structured."
```

### 3. Search Query Optimization
The prompt teaches better query formulation:
- BAD: "What are the main applications of AI in healthcare?"
- GOOD: "AI healthcare applications 2024"

### 4. Structured Synthesis
The final answer follows a logical structure:
1. Address key concepts
2. Present multiple perspectives
3. Cite sources
4. Acknowledge limitations

## Quick Start

```bash
# Navigate to simple-agent directory
cd samples/simple-agent

# Create .env if not already done (shared by all versions)
cp .env.example .env
# Edit .env with your settings

# Activate shared virtual environment
source venv/bin/activate

# Run v2 demo
cd v2
python examples/demo.py
```

## Configuration

Same as v1 - uses `LLM_BASE_URL`, `OPENAI_API_KEY`, `OPENAI_MODEL`, and `TAVILY_API_KEY`.

## Comparing v1 vs v2

Run both demos with the same question:

```bash
# Terminal 1: Run v1
cd samples/simple-agent/v1
python examples/demo.py

# Terminal 2: Run v2
cd samples/simple-agent/v2
python examples/demo.py
```

Observe the differences in:
- How the agent approaches the question
- The search queries it generates
- The reasoning it displays
- The structure of the final answer

## Next: v3 - Sub-Agent Architecture

v3 will introduce specialized sub-agents:
- Planner Agent: Decomposes questions and creates research plans
- Searcher Agent: Optimized for web searching
- Analyzer Agent: Deep analysis of content
- Synthesizer Agent: Combines findings into coherent answers
