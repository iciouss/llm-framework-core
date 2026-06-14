# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Development

```sh
uv venv && source .venv/bin/activate
uv pip install -e ".[std]"            # core + rag + oidc
uv sync --all-extras --group dev      # full dev environment
```

## Commands

```sh
# Unit tests (no LLM needed)
uv run pytest tests/unit tests/test_packaging.py -v

# Single test file / single test
uv run pytest tests/unit/test_agent.py -v
uv run pytest tests/unit/test_agent.py::test_name -v

# Integration tests (requires LLM_BASE_URL, LLM_API_KEY, LLM_MODEL in .env)
uv run pytest tests/integration -v -m integration

# Lint (check + auto-fix)
uv run ruff check llm_framework tests
uv run ruff check --fix llm_framework tests

# Type-check
uv run mypy llm_framework

# Security scan
uv run bandit -r llm_framework -ll

# Dependency audit
uv run deptry llm_framework tests

# Full diagnostic toolchain (ruff + bandit + radon + mypy + deptry + pytest-cov + pydeps)
bash tools/diagnose.sh
```

## Architecture

The package is `llm_framework/` with four layers:

- **`core/`** — Zero optional deps (only httpx). Contains the ReAct agent loop (`agent.py`), LLM HTTP client (`llm.py`), `@tool`/`@cached_tool` schema generation (`tools.py`), multi-agent orchestrator (`orchestrator.py`), history buffer (`history.py`), structural protocols (`protocols.py`), and observability primitives (`observability.py`).
- **`extensions/`** — Optional extras gated behind pip extras (`[mcp]`, `[rag]`, `[oidc]`, `[qdrant]`, `[server]`, and `[std]` which bundles `rag + oidc`). Contains MCP client/server, RAG with pluggable vector backends (sqlite-vec, Qdrant), auth (RBAC + OIDC), guardrails, and memory store. Extensions never import from `core/__init__.py` — they target submodules directly.
- **`tools/`** — `@tool`-decorated callables that run in-process alongside the agent. Built-ins: filesystem, shell (allowlisted read-only), web_fetch, memory, and math ops (`add_numbers` / `multiply_numbers` / `subtract_numbers`) in `builtins.py`.
- **`mcp_servers/`** — Out-of-process tool servers (knowledge, memory) exposing functionality via MCP stdio or HTTP transport.

Key architectural invariant: `core/` depends on nothing in `extensions/`. The boundary is enforced via structural `typing.Protocol` in `core/protocols.py` — concrete extension classes satisfy protocols without inheriting from them.

## Dependency Flow (DAG)

```
core/ ← extensions/ ← tools/ (that wrap extensions)
                    ← mcp_servers/
```

Imports must flow one way. Circular imports are a critical failure. Submodules never import from `__init__.py`.

## Coding Standards

- Python 3.13+. New/modified modules should use `from __future__ import annotations`.
- 100% type annotations on all signatures. `Any` is banned for internal modeling — use `Protocol`, `NamedTuple`, `dataclass`, or explicit generics.
- `ruff` for linting (rules: E, F, W, I, UP, B, SIM; E501 ignored). Line length 88.
- `mypy` strict on `llm_framework/` only.
- No mutable default arguments. No bare `except Exception:` without re-raise.
- Optional deps use try/except at module top → `None` sentinel, then `_optional.require()` at call site to raise with install hint.

## Commit Format

```
type(scope): lowercase imperative subject under 72 chars
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`.
Scopes: `agent`, `mcp`, `rag`, `observability`, `ci`, `repo`, `docs`.
Subject is conceptual only — no file paths or symbol names.

## Exemplars

The `exemplars/` directory contains canonical skeleton files for every repeated structural pattern. **Read the relevant exemplar before creating a new file.**

| Exemplar | Use when... |
|----------|-------------|
| `tool-definition.py` | Adding a new `@tool`-decorated callable in `tools/` |
| `mcp-server.py` | Creating a new MCP server in `mcp_servers/` |
| `extension-class.py` | Adding a class in `extensions/` |
| `optional-dep.py` | Gating an import behind a pip extra |
| `guardrail-factory.py` | Adding a new guardrail type |
| `vector-backend.py` | Adding a RAG storage backend |
| `unit-test-agent.py` | Testing agent behavior with `mock_llm` |
| `unit-test-tool.py` | Testing a `@tool` function |
| `unit-test-extension.py` | Testing an extension class |
| `example-script.py` | Adding a runnable example in `examples/` |

### Legacy patterns — do NOT replicate

If you encounter these in the codebase, **flag them to the user** rather than copying the style:

- **Extensions importing from `core/__init__.py`**: extensions must import submodules directly (e.g. `from llm_framework.core.tools import tool`), never the package root.

## Adding a Tool

1. Create a `@tool`-decorated function in `tools/`. The docstring's first line becomes the schema description; `Args:` block provides per-parameter descriptions.
2. Type hints on all parameters drive the JSON Schema generation (`tools.py:build_schema`).
3. Required params = no default value. Optional params = default value provided.

## Observability

Global hook system (`core/observability.py`): call `set_hook(hook)` with any `ObservabilityHook` protocol implementation. Events are dataclasses (`LLMCallEvent`, `AgentStepEvent`, `MCPEvent`, etc.) routed through `emit()`. No-op when no hook is registered.

## Testing Patterns

- `pytest-asyncio` is configured with `asyncio_mode = "auto"` — async test functions work without `@pytest.mark.asyncio`.
- `tests/conftest.py` provides shared fixtures:
  - `mock_llm` — factory for `MockLLMClient`: scriptable fake that returns canned responses in order. Accepts a list of strings (final answers) or raw response dicts.
  - `recording_hook` — installs a global `RecordingHook` that collects all observability events into `.events` for assertion.
- Unit tests must not require a live LLM. Use `MockLLMClient` to script tool-call sequences.

## Pre-commit Hook

Blocks `../` relative path sources in `pyproject.toml` `[tool.uv.sources]`. Install with `uv tool run pre-commit install`.
