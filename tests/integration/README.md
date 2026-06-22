# Integration Tests

These tests require a running LLM endpoint and **will not pass in CI** without real credentials.

## Prerequisites

Set the following environment variables (or populate `.env`):

```
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini
```

## Running

```sh
uv run pytest tests/integration -v -m integration
```

Run a single file:

```sh
uv run pytest tests/integration/test_guardrails_live.py -v
```

## What these tests do

| File | What it exercises |
|---|---|
| `test_guardrails_live.py` | `llm_guard()` with a real LLM evaluating content policy |
| `test_memory_live.py` | Agent + memory MCP server end-to-end (spawns `memory-server` from `examples/`) |
| `test_orchestrator_live.py` | Multi-agent orchestrator delegating between specialists |
| `test_rag_live.py` | RAG store ingestion + search + knowledge MCP server |
| `test_structured_output_live.py` | Structured JSON extraction via `response_format` |

All tests in this directory are marked with `@pytest.mark.integration`.
