# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Observability primitives: `emit`, `set_hook`, `on_step`, `ObservabilityContext`, and a typed event vocabulary (LLMCallEvent, EmbeddingEvent, RAGEvent, MCPEvent, GuardrailEvent, AgentStepEvent, OrchestratorEvent, PipelineStepEvent) for structured event emission from core call sites.
- `Agent.run(delegated_to=...)` parameter for caller correlation across `Orchestrator` sub-agents. Sub-agent events carry the delegating agent's name in their payload.
- `total_billable_tokens` field on `Agent.run()` result. Resolves the previous ambiguity in the `prompt + completion + reasoning` math: `reasoning_tokens` is a subset of `completion_tokens` and is not additive.
- `observability.print_hook()` helper for examples and ad-hoc debugging.
- `RecordingHook` pytest fixture in `tests/conftest.py`.
- `LICENSE` (MIT) and this `CHANGELOG.md`.
- `CLAUDE.md` agent instructions and `issues/` tracker at the repo root.
- `mypy` and `pytest-cov` added to the `dev` dependency group for CI type-checking and coverage reporting.
- GitHub Actions CI workflow (`.github/workflows/ci.yaml`) running ruff, mypy, and unit tests on every push to `main` and on pull requests.
- CI workflow extended with `gitleaks` (full-history secret scan, runs first to fail fast), `bandit` (Python security scan), and `deptry` (declared-dep audit, scoped to library + tests). `bandit` and `deptry` added to the `dev` group via `uv add`.

### Changed
- `Agent` and `Orchestrator` no longer accept an `on_event` callback. Subscribe via `llm_framework.observability.set_hook()` (global) or the per-instance `on_step` parameter.
- `Orchestrator.delegate()` no longer mutates sub-agent state at call time. Sub-agent events carry `delegated_to` in the payload instead.
- `Agent.run()` docstring now documents the token accounting contract explicitly: `completion_tokens` is OpenAI-compatible (includes reasoning); `total_billable_tokens` is the actual bill.
- All example scripts and integration tests migrated from the `on_event=...` pattern to the new hook pattern.
- Observability primitives moved from `llm_framework.observability` to `llm_framework.core.observability`; the old path remains as a silent backward-compat re-export.
- The internal `AgentEvent` TypedDict was removed from `core/agent.py`. The agent loop now constructs `AgentStepEvent` directly via a private helper, eliminating the dual event representation.
- `pyproject.toml` now declares `classifiers`, `keywords`, and a `[project.urls]` block (Homepage, Documentation, Issues) so the package renders correctly on PyPI.


### Fixed
- Token accounting no longer double-counts `reasoning_tokens` as a separate billable quantity. Consumers reading `prompt_tokens + completion_tokens + reasoning_tokens` were being charged twice for reasoning tokens; the new `total_billable_tokens` field gives the correct sum.
- Lazy `import dataclasses` inside `observability._attach_ctx` hoisted to the module-level imports.

[Unreleased]: https://github.com/moniente/llm-framework/compare/v0.0.0...HEAD
