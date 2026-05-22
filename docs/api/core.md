# Core

The core module contains the runtime primitives you use in almost every project.
It is intentionally small and dependency-light, so it can be the stable foundation for both simple scripts and larger multi-agent systems.

If you are unsure where to start, start in core: create an `LLMClient`, build an `Agent`, and add tools only as needed.

## LLMClient

`LLMClient` is the provider-agnostic HTTP client for chat completions and embeddings.
Use it directly when you need low-level model calls, or pass it to `Agent` and `Orchestrator` for higher-level workflows.

### ::: llm_framework.core.llm.LLMClient

---

## Agent

`Agent` implements the ReAct loop: reason, call tools, observe, and iterate to a final answer.
It is the main entry point for tool-using assistants and supports approvals, guardrails, and auth-aware tool filtering.

### ::: llm_framework.core.agent.Agent

---

## Orchestrator

`Orchestrator` is a supervisor/delegate layer for multi-agent task routing.
Use it when one prompt should be split across specialized agents with different prompts, tools, or responsibilities.

### ::: llm_framework.core.orchestrator.Orchestrator

---

## HistoryBuffer

`HistoryBuffer` maintains rolling multi-turn context with token-budget trimming.
Use it to keep conversations coherent while controlling prompt growth and cost.

### ::: llm_framework.core.history.HistoryBuffer

---

## Decorators

The decorators define how Python callables become model-callable tools.
Use `@tool` for schema generation from type hints and docstrings, and `@cached_tool` when deterministic tool calls should reuse prior results.

### ::: llm_framework.core.tools.tool

### ::: llm_framework.core.tools.cached_tool
