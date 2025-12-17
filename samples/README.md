# Agentic AI Samples

A collection of production-ready agentic AI systems demonstrating LLM function calling, autonomous decision-making, and observable AI architectures.

## 📚 Available Samples

### 1. [Market Research Agent](./market-research-agent/)

**Status:** ✅ Complete | **Complexity:** Advanced | **Agents:** 9

An autonomous market research system where the LLM decides which research tools to invoke via function calling.

**Key Features:**
- 🤖 **Pure Agentic Architecture**: LLM autonomously orchestrates research workflow
- 🔧 **32 Specialized Tools**: Across research, analysis, and domain-specific agents
- ⚡ **Parallel Execution**: ThreadPoolExecutor for concurrent tool calls
- 📊 **7 Agentic Agents**: Each with internal tool-based decision making
- 🎯 **vLLora Integration**: Full observability with custom headers
- 📝 **Professional Reports**: Executive summaries and detailed analysis

**What You'll Learn:**
- LLM function calling patterns
- Multi-agent system architecture
- Agentic loop implementation
- Parallel tool execution
- Observable AI systems
- Production-ready agent design

**Quick Start:**
```bash
cd market-research-agent
./setup.sh
python examples/demo.py
```

**Documentation:**
- [Quick Start Guide](./market-research-agent/docs/QUICKSTART.md)
- [Architecture Overview](./market-research-agent/README.md)
- [Agentic Orchestrator](./market-research-agent/docs/AGENTIC_ORCHESTRATOR.md)
- [Agent Architecture](./market-research-agent/docs/AGENTIC_AGENT_ARCHITECTURE.md)

---

### 2. [Sample Placeholder]

**Coming Soon**

More agentic AI samples will be added here demonstrating different patterns and use cases.

---

## 🎯 What Are These Samples?

These samples demonstrate **agentic AI systems** - AI agents that:

1. **Autonomously decide** which tools/actions to take
2. **Use LLM function calling** to invoke tools
3. **Execute tools in parallel** for efficiency
4. **Build context progressively** across iterations
5. **Make strategic decisions** based on objectives

## 🏗️ Common Patterns

All samples follow proven patterns:

### Agentic Loop Pattern
```python
while iteration < max_iterations:
    # 1. LLM decides which tools to call
    response = llm.chat.completions.create(
        messages=messages,
        tools=TOOL_DEFINITIONS,
        tool_choice="auto"
    )

    # 2. Execute tools (in parallel if multiple)
    if assistant_message.tool_calls:
        tool_results = execute_tools_parallel(tool_calls)
        messages.append(tool_results)
    else:
        # LLM is done
        break

    # 3. Build result from accumulated context
    return build_result(context)
```

### Parallel Execution Pattern
```python
with ThreadPoolExecutor(max_workers=num_tools) as executor:
    futures = {
        executor.submit(execute_tool, tc): tc
        for tc in tool_calls
    }
    for future in as_completed(futures):
        results.append(future.result())
```

### Tool Definition Pattern
```python
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "tool_name",
            "description": "What this tool does",
            "parameters": {
                "type": "object",
                "properties": {...},
                "required": [...]
            }
        }
    }
]
```

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- OpenAI API key or compatible LLM gateway
- (Optional) vLLora gateway for observability

### General Setup Pattern
```bash
# Clone the repository
git clone <repo-url>
cd samples/<sample-name>

# Set up environment
./setup.sh
# or manually:
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your API keys

# Run
python examples/demo.py
```

## 📖 Learn More

Each sample includes comprehensive documentation:
- **README.md** - Overview and quick start
- **docs/** - Detailed architecture and guides
- **examples/** - Runnable examples
- **src/** - Production-ready source code

## 🎓 Key Concepts

### Agentic AI
AI systems that autonomously decide their workflow rather than following predefined steps.

### Function Calling
LLM capability to invoke tools/functions with structured parameters.

### Observable AI
AI systems with full tracing and monitoring capabilities.

### Multi-Agent Systems
Multiple specialized AI agents working together.

### Parallel Execution
Running multiple operations simultaneously for performance.

## 📊 Complexity Levels

- **Beginner**: Single agent, few tools, straightforward workflow
- **Intermediate**: Multiple agents, moderate tool count, some parallel execution
- **Advanced**: Complex multi-agent systems, extensive tools, full parallel execution

## 🤝 Contributing

To add a new sample:
1. Create a new directory in `samples/`
2. Follow the structure of existing samples
3. Include comprehensive documentation
4. Add entry to this README

## 📝 License

Each sample may have its own license. Check individual sample directories.

## 🔗 Resources

- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)
- [vLLora Documentation](https://docs.vllora.dev)
- [Anthropic Claude](https://anthropic.com)
- [LangChain](https://langchain.com)

---

**Note**: These are educational samples demonstrating production-ready patterns. Adapt them to your specific use cases and requirements.
