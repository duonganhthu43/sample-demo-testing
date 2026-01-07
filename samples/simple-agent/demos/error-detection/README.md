# Demo: Error Detection

**Focus**: Tool execution failures and error detection

## What This Demo Shows

A simple agent with a **tool name mismatch** bug:
- Tool schema defines: `search_web`
- Tool executor expects: `web_search`
- Result: `"Unknown tool: search_web"` errors in traces

## Quick Start

```bash
cd samples/simple-agent
source venv/bin/activate
cd demos/error-detection
python examples/demo.py
```

## Expected Agent Analysis

When you ask Lucy: **"What's wrong with this run?"**

Lucy should detect:

| Span ID | Operation | Error | Severity |
|---------|-----------|-------|----------|
| `span-xxx` | openai | "Unknown tool: search_web" | High |

**Recommendation**: Register the `search_web` tool in the agent's executor, or rename the schema to `web_search`.

## The Bug

```python
# In tools.py - Schema says:
TOOL_DEFINITIONS = [{
    "function": {
        "name": "search_web",  # <-- LLM will call this
    }
}]

# In tools.py - Executor expects:
tools = {
    "web_search": web_search,  # <-- But this is registered
}
```

## Trace Pattern to Look For

```
Input (LLM tool call):
  {"tool": "search_web", "arguments": {"query": "..."}}

Output (Tool result):
  {"error": "Unknown tool: search_web"}
```
