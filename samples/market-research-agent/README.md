# Market Research Agent (vLLora Edition)

An **agentic AI system** for automated market research using **LLM function calling**, optimized for **vLLora** observability platform.

> **v2.0 Update:** Moved to pure agentic architecture! Hard-coded workflows removed. LLM now autonomously decides which tools to invoke. See [MIGRATION_GUIDE.md](docs/MIGRATION_GUIDE.md) for upgrade instructions.

## 🎯 Overview

This project demonstrates a production-ready agentic system where the **LLM autonomously decides which tools to invoke**:

- **🤖 Agentic Architecture**: LLM decides which research tools to use via function calling
- **13 Specialized Tools**: Research, analysis, financial, technology, sentiment, regulatory, quality review, and report generation
- **Autonomous Decision-Making**: No hard-coded workflows - LLM orchestrates itself
- **Adaptive Execution**: Tailors approach based on specific research objectives
- **Quality Assurance**: LLM can invoke quality review tool to ensure high standards
- **Comprehensive Analysis**: Deep-dive capabilities across financial, technical, market, sentiment, and regulatory dimensions
- **Professional Reports**: Generates executive summaries and detailed research reports
- **Full vLLora Integration**: All requests traced with `x-thread-id`, `x-run-id`, and `x-label` headers
- **OpenAI Compatible**: Works with any OpenAI-compatible LLM gateway

## 🏗️ Architecture

### Agentic System (LLM-Driven)

The system uses **LLM function calling** where the AI autonomously decides which tools to invoke:

```
┌──────────────────────────────────────────────────────┐
│           AGENTIC ORCHESTRATOR (LLM)                 │
│   Autonomously decides which tools to invoke         │
│   based on research objectives                       │
└────────────┬─────────────────────────────────────────┘
             │
             │ Function Calling (13 Tools Available)
             ▼
    ┌─────────────────────────────────────┐
    │         TOOL EXECUTOR               │
    │  Dispatches calls to agents         │
    └─────┬───────────────────────────────┘
          │
          │ Invokes as needed
          │
    ┌─────┴──────────────────────────────────────┐
    │                                             │
    ▼                                             ▼
┌────────────────┐  ┌──────────────────────────────┐
│ CORE AGENTS    │  │ SPECIALIZED AGENTS           │
├────────────────┤  ├──────────────────────────────┤
│ • Research     │  │ • Financial Analysis         │
│ • Analysis     │  │ • Technology Analysis        │
│ • Report Gen   │  │ • Market Sizing              │
│ • Quality Rev  │  │ • Sentiment Analysis         │
│                │  │ • Regulatory Analysis        │
└────────────────┘  └──────────────────────────────┘
```

### 13 Available Tools

The LLM can invoke these tools to conduct research:

**Research Tools:**
1. `research_company` - Comprehensive company information
2. `research_market` - Market and industry analysis
3. `research_competitors` - Competitor identification and analysis

**Analysis Tools:**
4. `perform_swot_analysis` - SWOT analysis
5. `perform_competitive_analysis` - Competitive positioning
6. `perform_trend_analysis` - Market trends and drivers

**Specialized Tools:**
7. `analyze_financials` - Financial deep-dive (revenue, funding, valuation)
8. `analyze_technology` - Technology stack and innovation
9. `analyze_market_size` - TAM/SAM/SOM calculations
10. `analyze_sentiment` - Customer sentiment and brand perception
11. `analyze_regulatory` - Regulatory landscape and compliance

**Quality & Output Tools:**
12. `review_research_quality` - Quality assurance and feedback
13. `generate_report` - Comprehensive report generation

### How It Works

1. **User provides objectives** → System defines research goals
2. **LLM receives tools** → AI sees all 13 available tools
3. **LLM decides autonomously** → Chooses which tools to call and in what order
4. **Tools execute** → Agents perform the actual work
5. **Results fed back** → LLM receives results and decides next step
6. **LLM continues or stops** → Repeats until research objectives met

**Key Benefits:**
- 🤖 **Fully Autonomous**: LLM makes all orchestration decisions
- 🎯 **Adaptive**: Approach tailored to each specific request
- ⚡ **Efficient**: Only invokes necessary tools
- 🧠 **Intelligent**: Builds context progressively
- 📊 **Observable**: Every tool call traced in vLLora

**See [AGENTIC_ORCHESTRATOR.md](AGENTIC_ORCHESTRATOR.md) for complete documentation.**

### vLLora Integration

All LLM requests include `x-thread-id`, `x-run-id`, and `x-label` headers for automatic trace grouping in vLLora's Debug tab!

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- **vLLora running** at http://localhost:9090
- Tavily API key (for real web search)

### Installation

```bash
# 1. Navigate to the sample directory
cd samples/market-research-agent

# 2. Create virtual environment
python3 -m venv venv

# 3. Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Configure environment
cp .env.example .env

# 6. Edit .env with your Tavily key
# The vLLora URL is already configured!
```

### Configuration

Your `.env` is pre-configured for vLLora:

```bash
# vLLora Gateway (already configured!)
LLM_BASE_URL=http://localhost:9090/v1
USE_LOCAL_GATEWAY=true

# Search API
TAVILY_API_KEY=your_tavily_key_here
```

### Run Demo

**Main Demo** (LLM-driven agentic research):
```bash
python examples/demo.py
```

**Simple Example** (Quick start):
```bash
python examples/simple_example.py
```

Then open **vLLora Dashboard** at http://localhost:3000 and check the **Debug tab** to see all traces!

## 📖 Usage Guide

### Basic Usage

```python
from src.agents import run_agentic_research

# LLM autonomously decides which tools to use based on objectives
result = run_agentic_research(
    company_name="Anthropic",
    industry="AI/LLM",
    objectives=[
        "Understand business model and competitive position",
        "Evaluate technology and AI safety approach",
        "Assess market opportunities"
    ],
    max_iterations=20
)

# See what the LLM decided to do
print(f"Tools called: {len(result.tool_calls_made)}")
print(f"Duration: {result.total_duration:.2f}s")

# View tool usage
for tc in result.tool_calls_made:
    print(f"  - {tc['tool']}")
```

### Advanced Usage

```python
from src.agents import AgenticOrchestrator
from src.utils import get_config

# Custom configuration
config = get_config()
orchestrator = AgenticOrchestrator(config, max_iterations=25)

result = orchestrator.execute_research(
    company_name="Stripe",
    industry="Fintech",
    objectives=[
        "Comprehensive competitive analysis",
        "Financial health and funding assessment",
        "Technology capabilities evaluation",
        "Customer sentiment analysis"
    ],
    additional_instructions="Focus on payment processing capabilities"
)

# Access detailed results
print(f"Iterations: {result.iterations}")
print(f"Context gathered:")
print(f"  - Research: {len(result.final_context['research'])}")
print(f"  - Analysis: {len(result.final_context['analysis'])}")
print(f"  - Specialized: {len(result.final_context['specialized'])}")
```

### Using Individual Agents

```python
from src.agents import ResearchAgent, AnalysisAgent
from src.utils import get_config

config = get_config()

# Research a company
research_agent = ResearchAgent(config)
company_data = research_agent.research_company("GitHub", depth="standard")

# Perform SWOT analysis
analysis_agent = AnalysisAgent(config)
swot = analysis_agent.perform_swot_analysis("GitHub", company_data.to_dict())
```

## 🔍 vLLora Observability

### How It Works

1. **Unique Thread ID**: Each research run generates a unique `thread_id`
2. **Unique Run ID**: Each research run also generates a unique `run_id`
3. **Agent Labels**: Each agent tags its requests with its name
4. **Header Injection**: All LLM requests include `x-thread-id`, `x-run-id`, and `x-label` headers
5. **Automatic Tracing**: vLLora captures and groups all requests

### View Traces

1. Open http://localhost:3000
2. Go to **Debug** tab
3. See all requests grouped by thread ID and run ID!

### What's Traced

Per research run (~15-30 requests):
- ✅ Company research LLM calls (labeled: `research_agent`)
- ✅ Market analysis LLM calls (labeled: `research_agent`)
- ✅ Competitor analysis LLM calls (labeled: `research_agent`)
- ✅ SWOT generation LLM calls (labeled: `analysis_agent`)
- ✅ Competitive analysis LLM calls (labeled: `analysis_agent`)
- ✅ Trend analysis LLM calls (labeled: `analysis_agent`)
- ✅ Report generation LLM calls (labeled: `report_agent`)

All grouped with headers:
- `x-thread-id`: Groups related workflow traces
- `x-run-id`: Groups all traces in the same execution run
- `x-label`: Tags each request with the agent name (research_agent, analysis_agent, report_agent)

## 📊 Output Files

Generated in `outputs/` directory:

```
outputs/
├── reports/               # Generated markdown reports
│   └── company_report_timestamp.md
└── logs/                  # Application logs (if enabled)
```

## ⚙️ Configuration

### Environment Variables

Key settings in `.env`:

```bash
# vLLora Gateway
LLM_BASE_URL=http://localhost:9090/v1
USE_LOCAL_GATEWAY=true
LLM_PROVIDER=openai

# Model Selection
OPENAI_MODEL=gpt-5  # Or any model on your gateway

# Search (Tavily for real results)
SEARCH_PROVIDER=tavily
TAVILY_API_KEY=your_key

# Agent Behavior
ENABLE_PARALLEL_EXECUTION=true  # Run agents in parallel
MAX_AGENT_ITERATIONS=10
AGENT_TIMEOUT=300  # Seconds
```

## 📁 Project Structure

```
market-research-agent/
├── src/
│   ├── agents/              # 4 specialized agents
│   │   ├── research_agent.py
│   │   ├── analysis_agent.py
│   │   ├── report_agent.py
│   │   └── orchestrator.py
│   ├── tools/               # Utility tools
│   │   ├── web_search.py    # Tavily/SerpAPI/Mock
│   │   ├── data_extractor.py
│   │   └── visualizer.py
│   └── utils/               # Configuration
│       ├── config.py
│       └── prompts.py
├── examples/                # Demo scripts
│   ├── demo.py              # Full demonstration
│   ├── simple_example.py    # Quick start
│   └── individual_agents.py # Custom workflows
├── outputs/                 # Generated files
├── requirements.txt
├── .env
└── README.md
```

## 🎨 Example Use Cases

### 1. Competitive Analysis
```python
result = run_market_research(
    company_name="Stripe",
    industry="Fintech",
    depth="deep"
)
```

### 2. Market Research
```python
research_agent = ResearchAgent()
market_data = research_agent.research_market("Cloud Computing", depth="deep")
```

### 3. Investment Research
```python
result = run_market_research(
    company_name="NVIDIA",
    industry="Semiconductors",
    depth="deep"
)
```

## 📈 Performance

Expected performance:
- **Quick research**: ~30-60 seconds, 5-10 LLM calls
- **Standard research**: ~2-5 minutes, 15-20 LLM calls
- **Deep research**: ~5-10 minutes, 30-40 LLM calls

All traces visible in vLLora Dashboard!

## 🔧 Extending the System

### Adding New Agents

```python
class CustomAgent:
    def __init__(self, config):
        self.config = config
        self.llm_client = config.get_llm_client()

    def perform_task(self, data):
        # Your logic here
        return result
```

### Adding New Tools

```python
# In src/tools/
class CustomTool:
    def process(self, input_data):
        # Tool logic
        return output
```

## 🎯 vLLora Features Used

- ✅ **OpenAI Compatible API**: Works out of the box
- ✅ **Built-in Observability**: Debug tab shows all requests
- ✅ **x-thread-id Support**: Groups related workflow requests
- ✅ **x-run-id Support**: Groups all traces in the same execution run
- ✅ **x-label Support**: Tags requests by agent name
- ✅ **Real-time Streaming**: See requests as they happen
- ✅ **Request/Response Details**: Full payload inspection
- ✅ **Duration Tracking**: Performance monitoring

## 📝 Notes

- **No observability code needed**: vLLora handles everything!
- **Thread ID, Run ID & Labels**: Automatically generated and included in headers
- **Agent Identification**: Each agent (Research, Analysis, Report) tags its own requests
- **Model Selection**: Use any model available on your vLLora gateway
- **Search**: Tavily recommended, mock mode available for testing

## 🤝 Contributing

This is a demo project showcasing agent patterns with vLLora integration.

## 📄 License

MIT License

## 🙋 Support

**For vLLora questions**: https://vllora.dev
**For agent questions**: Check example scripts in `examples/`

---

**Built specifically for vLLora observability platform** 🚀

All LLM requests automatically traced with `x-thread-id`, `x-run-id`, and `x-label` headers!
