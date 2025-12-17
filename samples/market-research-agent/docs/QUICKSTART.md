# Quick Start Guide - Local Setup

This guide helps you run the Market Research Agent with your local LLM gateway and observability platform.

## Prerequisites

- Python 3.9+
- Local LLM Gateway running at `http://localhost:9090/v1`
- Local OTEL Collector at `http://localhost:4317` (optional)

## Setup (2 minutes)

### 1. Install Dependencies

```bash
cd market-research-agent

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

### 2. Configuration

The `.env` file is already configured for your local setup:

```bash
# LLM Gateway
LLM_BASE_URL=http://localhost:9090/v1   ✓ Your local gateway
USE_LOCAL_GATEWAY=true                    ✓ Enabled

# OTEL Collector
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4317  ✓ Your OTEL endpoint

# Search APIs
SERPAPI_API_KEY=                          ✓ Empty = uses mock mode
```

**No API keys needed!** Everything runs locally.

## Run Demo (1 minute)

### Simple Test

```bash
python examples/simple_example.py
```

### Full Demo with Observability

```bash
python examples/demo.py
```

This will:
- Run complete market research on a company
- Make ~15 LLM calls to your local gateway
- Send traces to your OTEL collector at `localhost:4317`
- Generate a full report in `outputs/reports/`
- Export traces to `outputs/traces/demo_traces.json`
- Export metrics to `outputs/metrics/demo_metrics.json`

### Individual Agents

```bash
python examples/individual_agents.py
```

## What Gets Sent to Your Observability Platform

### Via OTEL (localhost:4317)

The system uses OpenTelemetry to send traces automatically:

```python
# Every LLM call creates a span with:
- operation.type: "completion"
- llm.model: "gpt-4-turbo-preview"
- llm.tokens: 2500
- llm.cost: 0.075
- duration_ms: 3000
```

### Via Custom Integration

You can also integrate directly with your platform by editing `src/observability/tracer.py` line 297:

```python
def _send_trace(self, trace_data: Dict[str, Any]):
    """Send trace to your observability platform"""
    # Add your platform's SDK here
    your_platform.send_trace(trace_data)
```

## Verify It's Working

### 1. Check LLM Gateway

```bash
# Your gateway should receive requests to:
# POST http://localhost:9090/v1/chat/completions
```

### 2. Check OTEL Collector

```bash
# Your OTEL collector should receive traces at:
# gRPC: localhost:4317
```

### 3. Check Outputs

```bash
# Generated files in outputs/
ls -la outputs/reports/     # Markdown reports
ls -la outputs/traces/      # Trace JSON files
ls -la outputs/metrics/     # Metrics JSON files
ls -la outputs/logs/        # Application logs
```

## Example Output

```
==================================================
Market Research: Anthropic
==================================================

✓ Using local LLM gateway: http://localhost:9090/v1

Phase 1: Planning
✓ Research plan created with 3 tasks

Phase 2: Research
✓ company research complete
✓ market research complete
✓ competitor research complete

Phase 3: Analysis
✓ SWOT analysis complete
✓ Competitive analysis complete
✓ Trend analysis complete

Phase 4: Report Generation
✓ Report generated

Execution Summary
Duration: 124.56s
LLM Calls: 15
Total Tokens: 25,420
Mode: parallel
```

## Troubleshooting

### LLM Gateway Connection Error

```bash
# Check your gateway is running:
curl http://localhost:9090/v1/models

# If not running, start your LLM gateway first
```

### OTEL Connection Error

```bash
# Check OTEL collector is running:
curl http://localhost:4317

# If traces aren't critical, you can disable:
# In .env: OBSERVABILITY_ENABLED=false
```

### Import Errors

```bash
# Make sure virtual environment is activated:
source venv/bin/activate

# Reinstall dependencies:
pip install -r requirements.txt
```

## Customization

### Change Company

```python
# In examples/simple_example.py
result = run_market_research(
    company_name="Your Company Name",  # ← Change this
    industry="Your Industry",           # ← And this
    depth="standard"
)
```

### Change Model

```bash
# In .env
OPENAI_MODEL=gpt-3.5-turbo  # Use different model on your gateway
```

### Disable Parallel Execution

```bash
# In .env
ENABLE_PARALLEL_EXECUTION=false  # Run agents sequentially
```

## Next Steps

1. ✅ Run the demo and verify traces reach your platform
2. ✅ Check `outputs/` directory for generated files
3. ✅ Customize company/industry in example scripts
4. ✅ Integrate your observability platform (see `INTEGRATION_GUIDE.md`)
5. ✅ Use for your demos!

## File Locations

```
Key Files:
├── .env                           ← Your configuration (pre-configured)
├── examples/demo.py               ← Full demo script
├── examples/simple_example.py     ← Quick test
├── src/observability/tracer.py    ← Integration point (line 297)
└── outputs/                       ← Generated files
```

## Support

- **Full Guide**: See `README.md`
- **Integration**: See `INTEGRATION_GUIDE.md`
- **Project Info**: See `PROJECT_SUMMARY.md`

---

**You're all set!** Your configuration is ready to use with your local LLM gateway and OTEL collector. Just run the demo! 🚀

```bash
python examples/demo.py
```
