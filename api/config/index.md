# Client Construction

`LLMClient.from_env()` reads `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`, and `CA_BUNDLE_PATH` from the environment (`.env` file loaded automatically) and constructs the client.

```python
from llm_framework.core import LLMClient

async with LLMClient.from_env() as client:
    ...
```

To use multiple endpoints in the same script, construct `LLMClient` directly:

```python
local = LLMClient(base_url="http://localhost:1234/v1", api_key="nokey", model="qwen3-4b")
remote = LLMClient(base_url="https://api.example.com", api_key="sk-...", model="gpt-4o")
```

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
