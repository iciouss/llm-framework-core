# Core

The core module contains the runtime primitives you use in almost every project. It is intentionally small and dependency-light, so it can be the stable foundation for both simple scripts and larger multi-agent systems.

If you are unsure where to start, start in core: create an `LLMClient`, build an `Agent`, and add tools only as needed.

## LLMClient

`LLMClient` is the provider-agnostic HTTP client for chat completions and embeddings. Use it directly when you need low-level model calls, or pass it to `Agent` and `Orchestrator` for higher-level workflows.

### llm_framework.core.llm.LLMClient

```python
LLMClient(base_url: str, api_key: str, model: str, timeout: float = 120.0, verify: str | bool = True)
```

Async HTTP client for OpenAI-compatible chat completion and embeddings endpoints.

Parameters:

| Name       | Type    | Description                                                                        | Default                                                                          |
| ---------- | ------- | ---------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- |
| `base_url` | `str`   | Base URL of the OpenAI-compatible API endpoint.                                    | *required*                                                                       |
| `api_key`  | `str`   | API key; sent as both Bearer token and x-api-key for cross-provider compatibility. | *required*                                                                       |
| `model`    | `str`   | Model identifier to use for all requests.                                          | *required*                                                                       |
| `timeout`  | `float` | HTTP request timeout in seconds (default 120).                                     | `120.0`                                                                          |
| `verify`   | \`str   | bool\`                                                                             | TLS verification — True for system CAs, False to skip, or a path to a CA bundle. |

#### from_env

```python
from_env() -> LLMClient
```

Construct from env vars; reads LLM_BASE_URL, LLM_API_KEY, LLM_MODEL, CA_BUNDLE_PATH.

#### chat_completions

```python
chat_completions(messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None, temperature: float = 0.7, max_tokens: int = 1024, max_retries: int = 3, response_format: dict[str, Any] | None = None) -> dict[str, Any]
```

Send a chat completion request with exponential backoff on transient server errors.

Parameters:

| Name              | Type                     | Description                                                           | Default                                                        |
| ----------------- | ------------------------ | --------------------------------------------------------------------- | -------------------------------------------------------------- |
| `messages`        | `list[dict[str, Any]]`   | Conversation history in OpenAI message format.                        | *required*                                                     |
| `tools`           | \`list\[dict[str, Any]\] | None\`                                                                | Optional list of JSON function schemas to expose to the model. |
| `temperature`     | `float`                  | Sampling temperature (default 0.7); use 0.0 for deterministic output. | `0.7`                                                          |
| `max_tokens`      | `int`                    | Maximum tokens in the response.                                       | `1024`                                                         |
| `max_retries`     | `int`                    | Retry attempts on 429/5xx errors with exponential backoff.            | `3`                                                            |
| `response_format` | \`dict[str, Any]         | None\`                                                                | Optional structured output schema (e.g. a json_schema object). |

Returns:

| Type             | Description                                                                |
| ---------------- | -------------------------------------------------------------------------- |
| `dict[str, Any]` | Raw OpenAI-compatible response dict with choices, usage, and model fields. |

#### embeddings

```python
embeddings(input_texts: list[str], max_retries: int = 3) -> list[list[float]]
```

Return one embedding vector per input text.

Parameters:

| Name          | Type        | Description                                                | Default    |
| ------------- | ----------- | ---------------------------------------------------------- | ---------- |
| `input_texts` | `list[str]` | List of strings to embed.                                  | *required* |
| `max_retries` | `int`       | Retry attempts on 429/5xx errors with exponential backoff. | `3`        |

Returns:

| Type                | Description                                                         |
| ------------------- | ------------------------------------------------------------------- |
| `list[list[float]]` | List of embedding vectors, one per input string, in the same order. |

______________________________________________________________________

## Agent

`Agent` implements the ReAct loop: reason, call tools, observe, and iterate to a final answer. It is the main entry point for tool-using assistants and supports approvals, guardrails, and auth-aware tool filtering.

### llm_framework.core.agent.Agent

```python
Agent(client: object, tools: list | None = None, max_steps: int = 10, max_tokens: int = 4096, temperature: float = 0.7, max_retries: int = 3, system_prompt: str | None = None, input_guards: list | None = None, output_guards: list | None = None, on_event: Callable[[AgentEvent], object] | None = None, approval_callback: object | None = None, approval_tools: list[str] | None = None, auth_gate: object | None = None)
```

ReAct agent that iterates tool calls until it reaches a final text answer.

Parameters:

| Name                | Type                               | Description                                                                                                         | Default                                                                                                                       |
| ------------------- | ---------------------------------- | ------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `client`            | `object`                           | An LLMClient instance for sending chat completion requests.                                                         | *required*                                                                                                                    |
| `tools`             | \`list                             | None\`                                                                                                              | List of @tool-decorated callables available during the ReAct loop.                                                            |
| `max_steps`         | `int`                              | Maximum reasoning iterations before returning a fallback answer (default 10).                                       | `10`                                                                                                                          |
| `max_tokens`        | `int`                              | Maximum tokens per LLM response (default 4096). Increase when the model must reproduce large tool results verbatim. | `4096`                                                                                                                        |
| `temperature`       | `float`                            | Sampling temperature (default 0.7). Use 0.0 for deterministic tasks like structured extraction or KQL generation.   | `0.7`                                                                                                                         |
| `max_retries`       | `int`                              | LLM request retry attempts with exponential backoff on 429/5xx errors (default 3).                                  | `3`                                                                                                                           |
| `system_prompt`     | \`str                              | None\`                                                                                                              | Persistent persona injected as the system message on every run() call; overridable per-call.                                  |
| `input_guards`      | \`list                             | None\`                                                                                                              | List of callables (str) -> str applied to the prompt before the LLM sees it. Raise to block, return to pass/transform.        |
| `output_guards`     | \`list                             | None\`                                                                                                              | List of callables (str) -> str applied to the final answer. Raise to block, return to pass/transform.                         |
| `on_event`          | \`Callable\[[AgentEvent], object\] | None\`                                                                                                              | Callable receiving structured event dicts at each step. None for silent operation.                                            |
| `approval_callback` | \`object                           | None\`                                                                                                              | Sync or async (name: str, args: dict) -> bool called before each tool runs. Return False to deny.                             |
| `approval_tools`    | \`list[str]                        | None\`                                                                                                              | Set of tool names that require approval. If None, every tool requires approval.                                               |
| `auth_gate`         | \`object                           | None\`                                                                                                              | An AuthGate instance that filters tool schemas and enforces access at execution time. None disables auth (all tools allowed). |

#### run

```python
run(prompt: str, system_prompt: str | None = None, prior_messages: list[dict] | None = None, auth_context: object | None = None) -> dict
```

Run the agent on a prompt and return the final answer with cumulative token usage.

Parameters:

| Name             | Type         | Description                  | Default                                                                                                                                         |
| ---------------- | ------------ | ---------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------- |
| `prompt`         | `str`        | The user's task or question. | *required*                                                                                                                                      |
| `system_prompt`  | \`str        | None\`                       | Override the agent's default persona for this call only.                                                                                        |
| `prior_messages` | \`list[dict] | None\`                       | Previous conversation turns to prepend; use with HistoryBuffer for multi-turn conversations.                                                    |
| `auth_context`   | \`object     | None\`                       | An AuthContext identifying the caller. When combined with auth_gate, unauthorized tools are hidden from the LLM and rejected at execution time. |

Returns:

| Type   | Description                                                                          |
| ------ | ------------------------------------------------------------------------------------ |
| `dict` | Dict with keys: answer (str), messages (list), context_tokens (current window size), |
| `dict` | prompt_tokens (cumulative billing total), completion_tokens, reasoning_tokens.       |

______________________________________________________________________

## Orchestrator

`Orchestrator` is a supervisor/delegate layer for multi-agent task routing. Use it when one prompt should be split across specialized agents with different prompts, tools, or responsibilities.

### llm_framework.core.orchestrator.Orchestrator

```python
Orchestrator(client: object, sub_agents: dict[str, Agent], max_steps: int = 10, max_tokens: int = 4096, max_retries: int = 3, history_max_tokens: int = 8000, on_event: object | None = None)
```

Supervisor agent that delegates tasks to named sub-agents via an injected delegate() tool.

Parameters:

| Name                 | Type               | Description                                                                                         | Default                                           |
| -------------------- | ------------------ | --------------------------------------------------------------------------------------------------- | ------------------------------------------------- |
| `client`             | `object`           | An LLMClient instance for the supervisor agent.                                                     | *required*                                        |
| `sub_agents`         | `dict[str, Agent]` | Mapping of agent name to Agent instance. Names are exposed to the supervisor as delegation targets. | *required*                                        |
| `max_steps`          | `int`              | Maximum supervisor reasoning iterations (default 10).                                               | `10`                                              |
| `max_tokens`         | `int`              | Maximum tokens per supervisor response (default 4096).                                              | `4096`                                            |
| `max_retries`        | `int`              | Retry attempts on transient API errors forwarded to the supervisor agent (default 3).               | `3`                                               |
| `history_max_tokens` | `int`              | Token budget for the supervisor history buffer (default 8000).                                      | `8000`                                            |
| `on_event`           | \`object           | None\`                                                                                              | Event callback forwarded to the supervisor agent. |

______________________________________________________________________

## HistoryBuffer

`HistoryBuffer` maintains rolling multi-turn context with token-budget trimming. Use it to keep conversations coherent while controlling prompt growth and cost.

### llm_framework.core.history.HistoryBuffer

```python
HistoryBuffer(max_messages: int | None = None, max_tokens: int | None = None)
```

Rolling message buffer that preserves the system message while trimming oldest history.

Parameters:

| Name           | Type  | Description | Default                                                                                                   |
| -------------- | ----- | ----------- | --------------------------------------------------------------------------------------------------------- |
| `max_messages` | \`int | None\`      | Maximum number of messages to retain. Oldest action/observation pairs are evicted first.                  |
| `max_tokens`   | \`int | None\`      | Soft token budget (char÷4 approximation with a 20% safety margin). The buffer trims to 80% of this value. |

#### messages

```python
messages: list[dict]
```

Current buffered messages after trimming.

#### extend

```python
extend(messages: list[dict])
```

Append messages (from an agent.run() result) and trim to configured limits.

#### get

```python
get() -> list[dict]
```

Return a copy of the current message history for use as prior_messages.

#### run

```python
run(agent: object, prompt: str, **kwargs: object) -> dict
```

Run the agent with buffered history, then extend the buffer automatically.

Parameters:

| Name       | Type     | Description                                    | Default    |
| ---------- | -------- | ---------------------------------------------- | ---------- |
| `agent`    | `object` | The Agent instance to run.                     | *required* |
| `prompt`   | `str`    | The user's task or question.                   | *required* |
| `**kwargs` | `object` | Forwarded to agent.run() (e.g. system_prompt). | `{}`       |

Returns:

| Type   | Description                                          |
| ------ | ---------------------------------------------------- |
| `dict` | The agent's result dict (same shape as agent.run()). |

#### clear

```python
clear()
```

Reset the buffer.

______________________________________________________________________

## Decorators

The decorators define how Python callables become model-callable tools. Use `@tool` for schema generation from type hints and docstrings, and `@cached_tool` when deterministic tool calls should reuse prior results.

### llm_framework.core.tools.tool

```python
tool(fn)
```

Decorator that attaches a JSON schema to a function, making it usable as an agent tool.

### llm_framework.core.tools.cached_tool

```python
cached_tool(fn=None, *, maxsize=128)
```

Decorator that caches tool results for the lifetime of the process; safe for both sync and async tools.
