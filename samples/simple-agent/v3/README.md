# Simple Agent v3 - Sub-Agent Architecture

This version introduces **specialized sub-agents** that work together.
Each agent has a focused role, leading to better research quality.

## What's Different from v1/v2?

| Aspect | v1/v2 | v3 (Sub-Agents) |
|--------|-------|-----------------|
| Architecture | Single agent | 4 specialized agents |
| Workflow | Ad-hoc | Structured phases |
| Specialization | None | Role-based prompts |
| Coordination | N/A | Orchestrator pattern |

## Sub-Agent Roles

### 1. PlannerAgent
**Role**: Research strategy and decomposition

- Analyzes the question
- Identifies key concepts
- Creates 2-4 sub-questions
- Generates optimized search queries

### 2. SearcherAgent
**Role**: Web search execution

- Executes planned searches
- Evaluates result quality
- Identifies promising sources
- Extracts detailed content when needed

### 3. AnalyzerAgent
**Role**: Content analysis and insight extraction

- Analyzes search results
- Extracts key facts and data
- Evaluates source credibility
- Records findings with attribution

### 4. SynthesizerAgent
**Role**: Answer creation

- Combines all findings
- Creates structured response
- Cites sources properly
- Acknowledges limitations

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
┌─────────────┐
│  Searcher   │ → Search results + content
└─────────────┘
    │
    ▼
┌─────────────┐
│  Analyzer   │ → Extracted insights
└─────────────┘
    │
    ▼
┌─────────────┐
│ Synthesizer │ → Final answer
└─────────────┘
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

# Run v3 demo
cd v3
python examples/demo.py
```

## Configuration

Same as v1/v2 - uses `LLM_BASE_URL`, `OPENAI_API_KEY`, `OPENAI_MODEL`, and `TAVILY_API_KEY`.

## Comparing v2 vs v3

Run both demos with the same question:

```bash
# Terminal 1: Run v2 (improved prompting)
cd samples/simple-agent/v2
python examples/demo.py

# Terminal 2: Run v3 (sub-agents)
cd samples/simple-agent/v3
python examples/demo.py
```

Observe the differences in:
- Clear phase separation (Plan → Search → Analyze → Synthesize)
- Specialized agent behaviors
- Information flow between agents
- Final answer structure

## Advantages of Sub-Agent Architecture

1. **Specialization**: Each agent is optimized for its role
2. **Modularity**: Easy to improve individual agents
3. **Clarity**: Clear workflow makes debugging easier
4. **Scalability**: Can add more specialized agents

## Limitations (addressed in v4)

- Still sequential execution
- Phases wait for each other
- No parallel searches

## Next: v4 - Parallel Execution

v4 will add concurrent execution:
- Multiple searches in parallel
- Async analysis
- Faster overall performance
