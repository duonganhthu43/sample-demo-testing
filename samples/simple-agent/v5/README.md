# Simple Agent v5 - Semantic Errors for Debug Testing

**WARNING: This version has INTENTIONAL BUGS for testing debug tracing agents.**

## Purpose

v5 is designed to help you test and validate debug tracing tools. It contains semantic errors that should be detectable by analyzing LLM request/response traces.

## Bugs Included

### Bug #1: Tool Name Mismatch

**Location:** `src/tools.py`

```python
# Schema defines this name:
TOOL_DEFINITIONS = [{
    "function": {
        "name": "search_web",  # <-- Schema says "search_web"
        ...
    }
}]

# But executor only knows this name:
def execute_tool(tool_name, arguments):
    tools = {
        "web_search": web_search,  # <-- Executor expects "web_search"
        ...
    }
```

**What traces show:**
- LLM calls tool named `"search_web"`
- Tool executor returns `{"error": "Unknown tool: search_web"}`
- Agent continues despite error (poor error handling)

### Bug #2: Conflicting System Prompt

**Location:** `src/agent.py`

```python
SYSTEM_PROMPT = """
1. You MUST use tools to gather information. Never answer without searching.
2. You should answer questions directly from your knowledge when possible.
3. Always call search_web at least 3 times before answering.
4. Be efficient - minimize tool calls and answer quickly.
...
"""
```

**What traces show:**
- System message contains contradictory instructions
- LLM behavior may be erratic or inconsistent
- May cause infinite loops or premature termination

### Bug #3: Missing Parameter in Schema

**Location:** `src/tools.py`

```python
# Function accepts this parameter:
def web_search(query: str, num_results: int = 5):
    ...

# But schema doesn't include it:
"parameters": {
    "properties": {
        "query": {"type": "string", ...}
        # Missing: "num_results"
    }
}
```

**What traces show:**
- LLM never sends `num_results` parameter
- Function always uses default value
- No way for LLM to request different result counts

### Bug #4: Response Format Mismatch

**Location:** `src/agent.py`

```python
# System prompt says:
"OUTPUT FORMAT:
- Respond with a JSON object containing your answer"

# But API call doesn't set:
response = self.client.chat.completions.create(
    model=self.model,
    messages=messages,
    tools=TOOL_DEFINITIONS,
    # Missing: response_format={"type": "json_object"}
)
```

**What traces show:**
- System prompt requests JSON output
- API call doesn't enforce JSON format
- Responses may not be valid JSON

### Bug #5: Poor Error Handling

**Location:** `src/agent.py`

```python
result = execute_tool(tool_name, arguments)

if isinstance(result, dict) and "error" in result:
    self._log(f"Tool error: {result['error']}")
    self.errors_encountered.append(...)
    # BUG: We don't inform the LLM about the error!
    # Agent continues as if nothing happened
```

**What traces show:**
- Tool returns error
- Error is logged but not sent to LLM
- LLM doesn't know the tool failed
- May cause repeated failures or wrong conclusions

## Quick Start

```bash
# Navigate to simple-agent directory
cd samples/simple-agent

# Create .env if not already done
cp .env.example .env
# Edit .env with your settings

# Activate shared virtual environment
source venv/bin/activate

# Run v5 demo
cd v5
python examples/demo.py
```

## Using with Debug Tracing Agent

After running the demo:

1. **Get the Thread ID** from the output
2. **Query your traces** using the thread ID
3. **Look for these patterns:**

```
Pattern: Tool Call Failure
- Request: {"tool": "search_web", "arguments": {...}}
- Response: {"error": "Unknown tool: search_web"}

Pattern: Contradictory Instructions
- System message contains:
  - "MUST use tools" AND "answer directly"
  - "at least 3 times" AND "minimize calls"

Pattern: Missing Schema Parameter
- Tool definition lacks "num_results"
- Function signature has num_results=5

Pattern: Format Mismatch
- System prompt mentions "JSON object"
- API call lacks response_format
```

## What Your Debug Agent Should Report

A good debug tracing agent should identify:

1. **Tool Execution Failures**
   - "search_web" tool calls failing with "Unknown tool" error
   - Suggests: Tool name mismatch between schema and executor

2. **Prompt Quality Issues**
   - Contradictory instructions in system message
   - Suggests: Review and simplify system prompt

3. **Schema Completeness**
   - Parameter used in code but missing from schema
   - Suggests: Add num_results to tool definition

4. **API Configuration**
   - JSON requested but response_format not set
   - Suggests: Add response_format parameter

5. **Error Propagation**
   - Errors logged but not sent to LLM
   - Suggests: Include error info in tool response

## Fixing the Bugs

To fix v5 and make it work like v1:

```python
# Fix #1: Change tool name in TOOL_DEFINITIONS
"name": "web_search"  # Match the function name

# Fix #2: Remove contradictions from system prompt
# Keep only consistent instructions

# Fix #3: Add missing parameter to schema
"num_results": {
    "type": "integer",
    "description": "Number of results to return"
}

# Fix #4: Add response_format if needed
response_format={"type": "json_object"}

# Fix #5: Send error info to LLM
messages.append({
    "role": "tool",
    "content": json.dumps({"error": result["error"], "suggestion": "try different tool"})
})
```

## The Complete Progression

| Version | Focus | Status |
|---------|-------|--------|
| v1 | Baseline | Working |
| v2 | Quality | Working |
| v3 | Organization | Working |
| v4 | Performance | Working |
| **v5** | **Debug Testing** | **Intentionally Broken** |

v5 is the only version with intentional bugs - use it to test your debugging tools!
