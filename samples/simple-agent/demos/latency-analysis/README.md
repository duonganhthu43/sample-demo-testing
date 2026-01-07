# Demo: Latency Analysis

**Focus**: Performance bottlenecks and latency percentiles (p50/p95/p99)

## What This Demo Shows

A multi-step agent with **varying latencies**:
- Multiple fast operations
- One slow "bottleneck" operation (simulated delay)
- Lucy should identify the slowest span and latency percentiles

## Quick Start

```bash
cd samples/simple-agent
source venv/bin/activate
cd demos/latency-analysis
python examples/demo.py
```

## Expected Agent Analysis

When you ask Lucy: **"Analyze the performance"** or **"Why is this slow?"**

Lucy should detect:

**Performance**:
| Span ID | Operation | Duration | % of Total |
|---------|-----------|----------|------------|
| `span-xxx` | slow_analysis | 3.5s | 70% |
| `span-yyy` | openai | 0.8s | 16% |
| `span-zzz` | web_search | 0.4s | 8% |

**Latency Percentiles**:
| Metric | Value |
|--------|-------|
| p50 | 400 ms |
| p95 | 3,200 ms |
| p99 | 3,500 ms |

**Recommendation**: The `slow_analysis` operation is a bottleneck (70% of total time). Consider optimizing or parallelizing this step.

## The Pattern

```python
# Fast operations (normal)
result = web_search(query)  # ~400ms

# SLOW operation (bottleneck)
time.sleep(3.0)  # Simulated heavy processing
result = analyze(data)  # ~3500ms total
```

## Trace Pattern to Look For

Look for spans with high `duration_ms` values:
- Most spans: 200-800ms
- Bottleneck span: 3000-4000ms
