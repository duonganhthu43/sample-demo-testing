# Multi-Level Agent Architecture

## Overview

The Market Research Agent system now features a **comprehensive multi-level agent architecture** that provides hierarchical coordination, specialized deep-dive analysis, quality assurance loops, and adaptive workflows.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SUPERVISOR AGENT                         │
│         (Strategic Planning & Coordination)                 │
│  • Creates research plans                                   │
│  • Coordinates agent execution                              │
│  • Makes adaptive decisions                                 │
└─────────────────────┬───────────────────────────────────────┘
                      │
         ┌────────────┼────────────┐
         │            │            │
    ┌────▼────┐  ┌───▼────┐  ┌───▼────────┐
    │Research │  │Analysis│  │Specialized │
    │ Agents  │  │ Agents │  │  Agents    │
    └────┬────┘  └───┬────┘  └───┬────────┘
         │           │            │
         │           │        ┌───▼────────────┐
         │           │        │ • Financial    │
         │           │        │ • Technology   │
         │           │        │ • Market Size  │
         │           │        │ • Sentiment    │
         │           │        │ • Regulatory   │
         │           │        └────────────────┘
         │           │
         └───────────┴────────────┐
                                  │
                         ┌────────▼────────┐
                         │ QUALITY         │
                         │ REVIEWER        │
                         │ • Reviews       │
                         │ • Gives Feedback│
                         │ • Triggers Loops│
                         └─────────────────┘
```

## Agent Hierarchy

### Level 1: Supervisor Agent
**Role**: Strategic Coordinator

**Capabilities**:
- Creates detailed research plans based on company and objectives
- Selects appropriate specialized agents
- Evaluates results and makes adaptive decisions
- Coordinates multi-iteration workflows

**When to use**: Always activated first to plan the research strategy

**Label**: `supervisor_agent`

### Level 2: Core Agents
**Agents**: ResearchAgent, AnalysisAgent, ReportAgent

**Role**: Fundamental research and analysis

**Capabilities**:
- Company research
- Market research
- Competitor analysis
- SWOT analysis
- Competitive analysis
- Trend analysis
- Report generation

**When to use**: Core agents run in every research project

**Labels**: `research_agent`, `analysis_agent`, `report_agent`

### Level 3: Specialized Agents
Deep-dive experts for specific domains

#### Financial Agent
**Label**: `financial_agent`

**Capabilities**:
- Revenue model analysis
- Funding history and valuation
- Financial health assessment
- Business model sustainability
- ROI and profitability analysis

**Use cases**:
- Investment research
- Financial due diligence
- Business model evaluation

#### Technology Agent
**Label**: `technology_agent`

**Capabilities**:
- Technology stack analysis
- R&D capabilities assessment
- Patent and IP research
- Technical differentiation analysis
- Innovation tracking

**Use cases**:
- Tech company evaluation
- Innovation assessment
- Technical competitive analysis

#### Market Sizing Agent
**Label**: `market_sizing_agent`

**Capabilities**:
- TAM/SAM/SOM calculations
- Market segmentation analysis
- Growth projections
- Market share analysis
- Addressable market assessment

**Use cases**:
- Market opportunity analysis
- Growth strategy planning
- Investment sizing

#### Sentiment Agent
**Label**: `sentiment_agent`

**Capabilities**:
- Customer feedback analysis
- Social media sentiment tracking
- Brand perception assessment
- Review analysis
- Reputation monitoring

**Use cases**:
- Brand health assessment
- Customer satisfaction analysis
- Reputation management

#### Regulatory Agent
**Label**: `regulatory_agent`

**Capabilities**:
- Regulatory landscape assessment
- Compliance requirement analysis
- Legal risk identification
- Policy impact analysis
- Licensing status review

**Use cases**:
- Compliance assessment
- Regulatory risk analysis
- Market entry evaluation

### Level 4: Quality Reviewer Agent
**Role**: Quality Assurance & Feedback

**Label**: `quality_reviewer_agent`

**Capabilities**:
- Multi-dimensional quality scoring
- Gap identification
- Completeness checking
- Feedback generation
- Refinement triggering

**Quality Dimensions**:
1. **Completeness**: Are all objectives addressed?
2. **Accuracy**: Is information credible and sourced?
3. **Depth**: Is analysis sufficiently insightful?
4. **Relevance**: Is content relevant to objectives?
5. **Clarity**: Is output well-organized?

**Threshold**: Default 0.7 (configurable)

**Actions**:
- Scores < threshold → Trigger refinement iteration
- Scores ≥ threshold → Approve and proceed

## Adaptive Workflows

### Workflow Features

1. **Strategic Planning**
   - Supervisor creates customized research plan
   - Determines which agents to activate
   - Sets priority areas

2. **Iterative Refinement**
   - Quality reviewer assesses outputs
   - Identifies gaps and weaknesses
   - Triggers additional research rounds
   - Max iterations: configurable (default: 2)

3. **Dynamic Agent Selection**
   - Supervisor selects specialized agents based on:
     - Company characteristics
     - Industry requirements
     - User objectives
     - Complexity assessment

4. **Feedback Loops**
   ```
   Research → Quality Review → Refinement → Research (if needed)
                              ↓
                           Complete (if quality met)
   ```

## Usage

### Basic Multi-Level Research

```python
from src.agents import run_multi_level_research

result = run_multi_level_research(
    company_name="Stripe",
    industry="Fintech",
    objectives=[
        "Analyze competitive position",
        "Evaluate technology capabilities",
        "Assess market opportunities"
    ],
    depth="deep",
    enable_quality_review=True,
    enable_specialized_analysis=True,
    max_iterations=2
)

# Access results
print(f"Iterations: {result.iterations}")
print(f"Specialized tasks: {len(result.specialized_results)}")
print(f"Quality score: {result.quality_reviews[-1]['scores']['overall']}")
```

### Advanced Usage with Custom Configuration

```python
from src.agents import MultiLevelOrchestrator
from src.utils import get_config

# Initialize with custom settings
config = get_config()
orchestrator = MultiLevelOrchestrator(
    config=config,
    max_iterations=3  # Allow up to 3 refinement rounds
)

# Execute research
result = orchestrator.execute_research(
    company_name="OpenAI",
    industry="AI/ML",
    objectives=["Comprehensive AI market analysis"],
    depth="deep",
    enable_quality_review=True,
    enable_specialized_analysis=True
)
```

### Using Individual Specialized Agents

```python
from src.agents import FinancialAgent, TechnologyAgent
from src.utils import get_config

config = get_config()

# Financial analysis
financial_agent = FinancialAgent(config)
financial_result = financial_agent.analyze_financials(
    company_name="Stripe",
    context={"research": research_data}
)

# Technology analysis
tech_agent = TechnologyAgent(config)
tech_result = tech_agent.analyze_technology(
    company_name="Stripe",
    context={"research": research_data}
)
```

## Configuration

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `company_name` | str | Required | Company to research |
| `industry` | str | Optional | Industry context |
| `objectives` | List[str] | Optional | Research objectives |
| `depth` | str | "deep" | Research depth: quick, standard, deep |
| `enable_quality_review` | bool | True | Enable quality assurance loops |
| `enable_specialized_analysis` | bool | True | Enable specialized agents |
| `max_iterations` | int | 2 | Maximum refinement iterations |

### Quality Threshold

Adjust quality threshold when initializing Quality Reviewer:

```python
from src.agents import QualityReviewerAgent

reviewer = QualityReviewerAgent(
    config=config,
    quality_threshold=0.8  # Stricter quality requirements
)
```

## Observability

All multi-level agents are fully instrumented with vLLora observability:

### Trace Headers

Every LLM request includes:
- `x-thread-id`: Workflow grouping
- `x-run-id`: Execution grouping
- `x-label`: Agent identification

### Agent Labels

- `supervisor_agent` - Strategic planning
- `research_agent` - Core research
- `analysis_agent` - Core analysis
- `financial_agent` - Financial analysis
- `technology_agent` - Technology analysis
- `market_sizing_agent` - Market sizing
- `sentiment_agent` - Sentiment analysis
- `regulatory_agent` - Regulatory analysis
- `quality_reviewer_agent` - Quality review
- `report_agent` - Report generation

### Viewing Traces

1. Open vLLora Dashboard: http://localhost:3000
2. Go to Debug tab
3. Filter by:
   - Thread ID (full workflow)
   - Run ID (single execution)
   - Agent label (specific agent)

## Performance

### Expected Execution Times

| Mode | Iterations | Specialized | Duration | LLM Calls |
|------|-----------|-------------|----------|-----------|
| Quick | 1 | No | 2-5 min | 10-15 |
| Standard | 1 | Yes | 5-10 min | 20-30 |
| Deep | 2 | Yes | 10-20 min | 40-60 |

### Optimization Tips

1. **Disable quality review** for faster execution:
   ```python
   run_multi_level_research(..., enable_quality_review=False)
   ```

2. **Selective specialized agents** - supervisor only activates needed agents

3. **Reduce iterations**:
   ```python
   run_multi_level_research(..., max_iterations=1)
   ```

## Examples

### Example 1: Comprehensive Company Analysis

```python
result = run_multi_level_research(
    company_name="Anthropic",
    industry="AI/LLM",
    objectives=[
        "Analyze market position and competitive advantages",
        "Evaluate technology and innovation capabilities",
        "Assess financial sustainability and funding",
        "Understand brand perception and customer sentiment",
        "Identify regulatory challenges and compliance"
    ],
    depth="deep",
    enable_quality_review=True,
    enable_specialized_analysis=True,
    max_iterations=2
)
```

### Example 2: Quick Market Entry Assessment

```python
result = run_multi_level_research(
    company_name="NewStartup",
    industry="SaaS",
    objectives=[
        "Assess market size and opportunity",
        "Identify key competitors and positioning",
        "Understand regulatory requirements"
    ],
    depth="standard",
    enable_quality_review=False,  # Skip for speed
    enable_specialized_analysis=True,
    max_iterations=1
)
```

### Example 3: Investment Due Diligence

```python
result = run_multi_level_research(
    company_name="TargetCompany",
    industry="Fintech",
    objectives=[
        "Financial health and revenue model analysis",
        "Technology moat and IP assessment",
        "Market opportunity and growth potential",
        "Customer satisfaction and retention",
        "Regulatory compliance and risks"
    ],
    depth="deep",
    enable_quality_review=True,
    enable_specialized_analysis=True,
    max_iterations=3  # Extra thorough
)
```

## Extending the System

### Adding New Specialized Agents

1. Create new agent class in `specialized_agents.py`:

```python
class CustomAgent:
    def __init__(self, config):
        self.config = config
        self.llm_client = config.get_llm_client(label="custom_agent")
        self.llm_params = config.get_llm_params()

    def analyze(self, company_name, context):
        # Your analysis logic
        return SpecializedResult(...)
```

2. Add to multi-level orchestrator's `_execute_specialized_phase()`

3. Update supervisor to include in planning

### Custom Quality Metrics

Extend QualityReviewerAgent to add custom quality dimensions or modify scoring logic.

## Troubleshooting

### Common Issues

**Q: Quality review always triggers refinement**
- A: Lower quality threshold or improve initial research depth

**Q: Too many LLM calls / too slow**
- A: Disable quality review or reduce max_iterations
- Disable specialized analysis if not needed

**Q: Specialized agents not running**
- A: Ensure objectives clearly indicate need for specialized analysis
- Supervisor may not select them based on plan

**Q: Results not comprehensive enough**
- A: Set depth="deep" and max_iterations=2 or higher
- Enable all specialized agents
- Add more specific objectives

## Best Practices

1. **Clear Objectives**: Provide specific, measurable research objectives
2. **Appropriate Depth**: Match depth to time/cost constraints
3. **Quality Review**: Enable for production research, disable for prototyping
4. **Specialized Agents**: Let supervisor decide, or manually specify
5. **Monitor Traces**: Use vLLora to track execution and optimize
6. **Iterate**: Start with quick mode, refine to deep as needed

## Summary

The multi-level agent architecture provides:

✅ **Hierarchical Coordination** - Supervisor plans and manages workflow
✅ **Specialized Expertise** - 5 specialized agents for deep-dive analysis
✅ **Quality Assurance** - Automatic review and refinement loops
✅ **Adaptive Workflows** - Dynamic agent selection and execution
✅ **Complete Observability** - Full vLLora tracing and monitoring
✅ **Production Ready** - Robust, tested, and extensible

Use `python examples/multi_level_demo.py` to see it in action!
