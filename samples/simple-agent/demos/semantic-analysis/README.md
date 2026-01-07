# Demo: Semantic Analysis

**Focus**: Contradictory prompt instructions and prompt quality issues

## What This Demo Shows

An agent with a **badly written system prompt** containing:
- Contradictory instructions ("MUST use tools" vs "answer directly")
- Conflicting requirements ("at least 3 times" vs "minimize calls")
- Format confusion ("JSON" vs "plain text")

## Quick Start

```bash
cd samples/simple-agent
source venv/bin/activate
cd demos/semantic-analysis
python examples/demo.py
```

## Expected Agent Analysis

When you ask Lucy: **"Is there anything wrong?"** or **"Analyze this run"**

Lucy should detect:

| Span ID | Pattern | Source | Severity |
|---------|---------|--------|----------|
| `span-xxx` | "MUST use tools" vs "answer directly" | system_prompt | High |
| `span-xxx` | "at least 3 times" vs "minimize calls" | system_prompt | High |
| `span-xxx` | "JSON" vs "plain text" format | system_prompt | Medium |

**Recommendation**: Remove contradictory instructions from system prompt. Keep consistent directives.

## The Bug

```python
SYSTEM_PROMPT = """
IMPORTANT INSTRUCTIONS (these conflict with each other!):

1. You MUST use tools to gather information. Never answer without searching.
2. You should answer questions directly from your knowledge. Don't waste time.
3. Always call search at least 3 times before answering.
4. Be efficient - minimize tool calls and answer quickly.
5. Respond with a JSON object containing your answer.
6. Just respond naturally in plain text.
"""
```

## Contradiction Patterns to Detect

| Instruction A | Instruction B | Issue |
|--------------|---------------|-------|
| "MUST use tools" | "answer directly" | Conflicting behavior |
| "at least 3 times" | "minimize calls" | Conflicting counts |
| "JSON object" | "plain text" | Format confusion |
| "thorough research" | "quick answer" | Quality vs speed |
