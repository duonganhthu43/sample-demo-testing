# Demo: Cost Analysis

**Focus**: Multi-model cost breakdown and optimization suggestions

## What This Demo Shows

A multi-step agent that uses **expensive GPT-4** for analysis and **cheap GPT-4o-mini** for searches:
- GPT-4 calls accumulate high costs
- GPT-4o-mini calls are cheap
- Lucy should identify which model is the cost culprit

## Quick Start

```bash
cd samples/simple-agent
source venv/bin/activate
cd demos/cost-analysis
python examples/demo.py
```

## Expected Agent Analysis

When you ask Lucy: **"Why is this so expensive?"** or **"Analyze the cost"**

Lucy should detect:

| Model | Input Tokens | Output Tokens | Cost |
|-------|--------------|---------------|------|
| gpt-4 | 3,500 | 1,000 | $0.12 |
| gpt-4o-mini | 1,500 | 500 | $0.003 |
| **Total** | **5,000** | **1,500** | **$0.123** |

**Recommendation**: Switch non-critical calls to `gpt-4o-mini` for 97%+ cost savings.

## The Pattern

```python
# Expensive: GPT-4 for "analysis" (overkill)
response = client.chat.completions.create(
    model="gpt-4",  # $0.03/1K input, $0.06/1K output
    messages=analysis_messages
)

# Cheap: GPT-4o-mini for search (appropriate)
response = client.chat.completions.create(
    model="gpt-4o-mini",  # $0.00015/1K input, $0.0006/1K output
    messages=search_messages
)
```

## Cost Comparison

| Model | Input Cost | Output Cost | 100x Cheaper? |
|-------|------------|-------------|---------------|
| gpt-4 | $0.03/1K | $0.06/1K | - |
| gpt-4o-mini | $0.00015/1K | $0.0006/1K | Yes! |
