# vLLora Agent Analysis Demos

Four focused demo scenarios to showcase Lucy's analysis capabilities.

## Quick Start

```bash
cd samples/simple-agent
source venv/bin/activate

# Run any demo
cd demos/error-detection && python examples/demo.py
cd demos/cost-analysis && python examples/demo.py
cd demos/latency-analysis && python examples/demo.py
cd demos/semantic-analysis && python examples/demo.py
```

## Demo Overview

| Demo | Focus | User Question | Expected Output |
|------|-------|---------------|-----------------|
| **error-detection** | Tool errors | "What's wrong?" | Unknown tool error table |
| **cost-analysis** | Cost breakdown | "Why expensive?" | Cost by model table |
| **latency-analysis** | Performance | "Analyze performance" | Latency percentiles (p50/p95/p99) |
| **semantic-analysis** | Prompt issues | "Is anything wrong?" | Contradictory instructions table |
| **hidden-issues** | Lucy vs Human | "Is anything wrong?" | 5+ hidden issues humans miss |

---

## 1. Error Detection Demo

**Path**: `demos/error-detection`

**Bug**: Tool name mismatch
- Schema defines: `search_web`
- Executor expects: `web_search`
- Result: `"Unknown tool: search_web"` errors

**Run**:
```bash
cd demos/error-detection && python examples/demo.py
```

**Ask Lucy**: "What's wrong with this run?"

**Expected**:
```
## Errors & Issues
| Span ID | Operation | Error | Severity |
|---------|-----------|-------|----------|
| span-xxx | openai | "Unknown tool: search_web" | High |

## Recommendations
- Register the search_web tool or rename schema to web_search
```

---

## 2. Cost Analysis Demo

**Path**: `demos/cost-analysis`

**Pattern**: Multi-model usage
- GPT-4 for "analysis" (expensive)
- GPT-4o-mini for search (cheap)

**Run**:
```bash
cd demos/cost-analysis && python examples/demo.py
```

**Ask Lucy**: "Why is this so expensive?"

**Expected**:
```
## Cost
| Model | Input Tokens | Output Tokens | Cost |
|-------|--------------|---------------|------|
| gpt-4 | 3,500 | 1,000 | $0.12 |
| gpt-4o-mini | 1,500 | 500 | $0.003 |
| **Total** | | | **$0.123** |

## Recommendations
- Switch gpt-4 calls to gpt-4o-mini (97% cost savings)
```

---

## 3. Latency Analysis Demo

**Path**: `demos/latency-analysis`

**Pattern**: Performance bottleneck
- Fast operations: ~300ms
- Slow operation: ~3000ms (bottleneck)

**Run**:
```bash
cd demos/latency-analysis && python examples/demo.py
```

**Ask Lucy**: "Analyze the performance"

**Expected**:
```
## Performance
| Span ID | Operation | Duration | % of Total |
|---------|-----------|----------|------------|
| span-xxx | slow_analysis | 3.5s | 70% |
| span-yyy | web_search | 0.3s | 6% |

## Latency Percentiles
| Metric | Value |
|--------|-------|
| p50 | 300 ms |
| p95 | 3,200 ms |
| p99 | 3,500 ms |

## Recommendations
- slow_analysis is a bottleneck (70% of time)
```

---

## 4. Semantic Analysis Demo

**Path**: `demos/semantic-analysis`

**Bug**: Contradictory prompt instructions
- "MUST use tools" vs "answer directly"
- "at least 3 times" vs "minimize calls"
- "JSON object" vs "plain text"

**Run**:
```bash
cd demos/semantic-analysis && python examples/demo.py
```

**Ask Lucy**: "Is there anything wrong?"

**Expected**:
```
## Semantic Issues
| Span ID | Pattern | Source | Severity |
|---------|---------|--------|----------|
| span-xxx | "MUST use tools" vs "answer directly" | system_prompt | High |
| span-xxx | "at least 3 times" vs "minimize calls" | system_prompt | High |

## Recommendations
- Remove contradictory instructions from system prompt
```

---

## 5. Hidden Issues Demo (Lucy vs Human)

**Path**: `demos/hidden-issues`

**Pattern**: Silent failures and buried errors
- Tools return "success" but content has problems
- Errors buried in 3000+ character responses
- Issues spread across 5+ spans

**Run**:
```bash
cd demos/hidden-issues && python examples/demo.py
```

**Challenge**: Try to manually find all issues in traces first, then ask Lucy!

**Ask Lucy**: "Is there anything wrong?"

**Expected**:
```
## Semantic Issues
| Span ID | Pattern | Source | Severity |
|---------|---------|--------|----------|
| span-1 | "could not find any relevant results" | output | Medium |
| span-2 | "Failed to retrieve primary source" | output | High |
| span-3 | "checksum mismatch detected" | output | High |
| span-4 | "Rate limited, serving stale cache" | output | Medium |
| span-5 | "confidence below threshold (0.45)" | output | Medium |

## Recommendations
- Multiple silent failures detected in "successful" responses
- Check API rate limits and data freshness
- Validate data sources (2019 cache detected)
```

**Why humans miss these**:
- All responses show `"status": "success"`
- Errors buried in long content (3000+ chars)
- Issues spread across 7 tool calls
- Human would need to read every character of every response

---

## Demo Flow (Recommended Order)

1. **Error Detection** (30s) - Clear, visual bug detection
2. **Cost Analysis** (45s) - Direct ROI demonstration
3. **Latency Analysis** (45s) - Performance insights with percentiles
4. **Semantic Analysis** (30s) - Advanced prompt quality analysis
5. **Hidden Issues** (60s) - Lucy vs Human challenge (best for last!)

## Labels for Filtering

Each demo uses a unique label for easy filtering in vLLora:

| Demo | Label |
|------|-------|
| error-detection | `demo-error-detection` |
| cost-analysis | `demo-cost-analysis` |
| latency-analysis | `demo-latency-analysis` |
| semantic-analysis | `demo-semantic-analysis` |
| hidden-issues | `demo-hidden-issues` |

Use Lucy: "Show me traces with label demo-error-detection"
