# Demo: Hidden Issues (Lucy vs Manual Trace Reading)

**Focus**: Subtle issues that humans would miss but Lucy detects automatically

## Why This Demo?

When reading traces manually, humans:
- **Skim long responses** - miss errors buried in 5000+ character outputs
- **Lose track across spans** - can't remember if same error appeared 10 spans ago
- **Miss "silent failures"** - tool returns HTTP 200 but content says "not found"
- **Can't aggregate costs** - don't mentally sum costs across 15 model calls

Lucy automatically:
- Scans ALL content for error patterns
- Tracks repeated failures across spans
- Detects semantic errors even in "successful" responses
- Aggregates metrics (cost, latency, tokens)

## What This Demo Shows

An agent that **looks successful** but has hidden issues:

1. **Silent Failures**: Tools return success (no `error` field) but response contains "could not find", "no results", "failed to retrieve"
2. **Buried Errors**: Error message hidden in middle of 3000+ character JSON response
3. **Repeated Pattern**: Same issue happens 5+ times across different spans
4. **Looks Normal**: Agent completes, provides an answer, no obvious errors in trace list

## Quick Start

```bash
cd samples/simple-agent
source venv/bin/activate
cd demos/hidden-issues
python examples/demo.py
```

## The Challenge

After running the demo, try to find the issues by:
1. Opening vLLora traces
2. Manually reading through each span
3. Can you spot all 5+ hidden errors?

Then ask Lucy: **"Is there anything wrong with this run?"**

Lucy should find all issues in seconds.

## Hidden Issues in This Demo

### Issue 1: Silent Search Failure
```json
{
  "status": "success",
  "results": [],
  "message": "Search completed but could not find any relevant results for the query"
}
```
- No `error` field - looks successful
- But `results` is empty and message indicates failure
- Human skimming would see "success" and move on

### Issue 2: Error Buried in Long Response
```json
{
  "status": "success",
  "data": {
    "content": "... 2000 characters of valid content ... WARNING: Failed to retrieve primary source, using cached fallback from 2019 which may be outdated ... 1000 more characters ..."
  }
}
```
- Buried warning in middle of long content
- Human would need to read every character to find it

### Issue 3: Repeated "Not Found" Pattern
The agent calls search 5+ times, each with subtle "not found" in results:
- Span 1: "No matching documents found"
- Span 3: "Query returned empty results"
- Span 5: "Could not locate requested information"
- Human loses track; Lucy counts all occurrences

### Issue 4: Gradual Degradation
Tool responses get progressively worse:
- First call: Full results
- Second call: Partial results
- Third call: "Rate limited, returning cached data"
- Fourth call: Empty results

## Expected Lucy Output

```
## Summary
Run completed but has **5 semantic issues** detected in responses.

## Semantic Issues
| Span ID | Pattern | Source | Severity |
|---------|---------|--------|----------|
| span-1 | "could not find any relevant results" | output | Medium |
| span-3 | "Failed to retrieve primary source" | output | High |
| span-5 | "No matching documents found" | output | Medium |
| span-7 | "Rate limited, returning cached" | output | Medium |
| span-9 | "Query returned empty results" | output | Medium |

## Recommendations
- Investigate why searches are returning empty/cached results
- Check rate limiting on external APIs
- Validate data freshness (2019 cached fallback detected)
```

## Why Humans Miss These

| Issue Type | Why Human Misses | Why Lucy Catches |
|------------|------------------|------------------|
| Silent failure | Sees "success", moves on | Scans content for error patterns |
| Buried error | Doesn't read 3000 char response | Pattern matches entire content |
| Repeated pattern | Forgets span 1 by span 10 | Aggregates across all spans |
| Gradual degradation | Each span looks "okay" | Tracks trends and counts |
