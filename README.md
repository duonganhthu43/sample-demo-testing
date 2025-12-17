# Agentic AI Samples Collection

**Production-ready examples of agentic AI systems using LLM function calling and autonomous decision-making.**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 🎯 What's This?

This repository contains **production-ready agentic AI samples** demonstrating how to build AI systems where the LLM autonomously decides which tools to invoke, rather than following hard-coded workflows.

## 📚 Samples

Explore our collection of agentic AI implementations:

### [📊 Market Research Agent](./samples/market-research-agent/)

**An autonomous market research system with 9 specialized agents and 32 tools.**

- ✅ Complete and Production-Ready
- 🤖 Pure agentic architecture
- ⚡ Parallel tool execution
- 📊 Full vLLora observability
- 🎯 7 agentic agents (ResearchAgent, AnalysisAgent, Financial, Technology, Market Sizing, Sentiment, Regulatory)

**Perfect for learning:**
- LLM function calling patterns
- Multi-agent architectures
- Agentic loop implementation
- Observable AI systems

[**→ View Sample**](./samples/market-research-agent/) | [**→ Quick Start**](./samples/market-research-agent/docs/QUICKSTART.md)

---

### 🔮 More Samples Coming Soon

Additional samples demonstrating different agentic patterns and use cases will be added.

## 🚀 Quick Start

```bash
# Clone the repository
git clone <your-repo-url>

# Navigate to a sample
cd samples/market-research-agent

# Set up and run
./setup.sh
python examples/demo.py
```

## 🎓 What You'll Learn

Across all samples, you'll learn:

1. **Agentic Architecture** - How to build AI that decides its own workflow
2. **LLM Function Calling** - Using tools via structured parameters
3. **Parallel Execution** - Running multiple tools simultaneously
4. **Multi-Agent Systems** - Coordinating specialized AI agents
5. **Observable AI** - Full tracing and monitoring
6. **Production Patterns** - Battle-tested architectural patterns

## 🏗️ Architecture Patterns

All samples follow proven architectural patterns:

### The Agentic Loop
```python
# LLM decides → Execute tools → Build context → Repeat until done
while not done:
    response = llm.call_with_tools(messages, tools)
    if response.tool_calls:
        results = execute_tools_parallel(response.tool_calls)
        messages.append(results)
    else:
        done = True
return synthesize(context)
```

### Tool Definition
```python
{
    "type": "function",
    "function": {
        "name": "tool_name",
        "description": "What the tool does",
        "parameters": {...}
    }
}
```

### Parallel Execution
```python
with ThreadPoolExecutor(max_workers=n) as executor:
    futures = [executor.submit(tool, args) for tool in tools]
    results = [f.result() for f in as_completed(futures)]
```

## 📊 Sample Comparison

| Sample | Agents | Tools | Complexity | Status |
|--------|--------|-------|------------|--------|
| Market Research Agent | 9 | 32 | Advanced | ✅ Complete |
| *More coming soon* | - | - | - | 🔜 Planned |

## 🎯 Use Cases

These samples are perfect for:

- **Learning** - Understanding agentic AI architecture
- **Reference** - Building your own agentic systems
- **Production** - Adapting for real-world applications
- **Research** - Exploring LLM capabilities

## 🛠️ Technology Stack

- **Python 3.8+**
- **OpenAI API** (or compatible)
- **vLLora** (optional, for observability)
- **ThreadPoolExecutor** (parallel execution)
- **Function Calling** (tool invocation)

## 📖 Documentation

Each sample includes:
- 📄 **README.md** - Overview and quick start
- 📚 **docs/** - Detailed architecture guides
- 💻 **examples/** - Runnable code examples
- 🧪 **tests/** - Verification tests

## 🤝 Contributing

Contributions are welcome! To add a new sample:

1. Create a new directory in `samples/`
2. Follow the existing sample structure
3. Include comprehensive documentation
4. Submit a pull request

## 📝 License

See individual sample directories for specific licenses.

## 🔗 Resources

- [OpenAI Function Calling Guide](https://platform.openai.com/docs/guides/function-calling)
- [vLLora Documentation](https://docs.vllora.dev)
- [Agentic AI Patterns](https://www.anthropic.com/research)

## 🌟 Highlights

### Why These Samples?

✅ **Production-Ready** - Not just tutorials, but real implementations
✅ **Best Practices** - Following industry-standard patterns
✅ **Well-Documented** - Comprehensive guides and examples
✅ **Observable** - Full tracing and monitoring support
✅ **Scalable** - Designed for real-world use cases

### What Makes Them Unique?

- **Pure Agentic Architecture** - No hard-coded workflows
- **Parallel Execution** - Performance-optimized
- **Progressive Context Building** - Intelligent synthesis
- **Observable by Design** - Built-in monitoring
- **Modular and Extensible** - Easy to customize

---

**Ready to build agentic AI systems?** [**Get Started →**](./samples/)

---

<div align="center">
Made with ❤️ for the AI community
</div>
