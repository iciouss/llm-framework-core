# Extensions

Extensions are optional modules that add capabilities beyond the core runtime while keeping dependencies explicit. Use extensions when you need integration features like MCP connectivity, RAG storage, policy-based auth, or output safeguards.

## MCP

MCP extensions connect your agents to out-of-process tool servers over stdio or streamable HTTP. Use `MCPClient`/`MCPManager` to consume tools from any MCP server. Use `MCPServer`/`MCPContext` to build and expose your own.

### llm_framework.extensions.mcp.MCPClient

```python
MCPClient(transport: str, timeout: float | None = None, **kwargs)
```

Manages a single MCP server connection over stdio or streamable-HTTP transport.

#### stdio

```python
stdio(command: str, args: list[str] | None = None, env: dict | None = None, timeout: float = 60.0)
```

Connect to an MCP server running as a subprocess over stdio.

Parameters:

| Name      | Type        | Description                                                                     | Default                                                                |
| --------- | ----------- | ------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| `command` | `str`       | Executable to launch (e.g. "uv").                                               | *required*                                                             |
| `args`    | \`list[str] | None\`                                                                          | Command-line arguments (e.g. ["run", "memory-server"]).                |
| `env`     | \`dict      | None\`                                                                          | Optional environment variables merged into the subprocess environment. |
| `timeout` | `float`     | Per-call timeout in seconds (default 60). Subprocess is killed on context exit. | `60.0`                                                                 |

#### http

```python
http(url: str, timeout: float = 300.0)
```

Connect to an MCP server over streamable HTTP.

Parameters:

| Name      | Type    | Description                                                                                 | Default    |
| --------- | ------- | ------------------------------------------------------------------------------------------- | ---------- |
| `url`     | `str`   | Full URL to the MCP endpoint (e.g. http://localhost:8080/mcp).                              | *required* |
| `timeout` | `float` | Request timeout in seconds (default 300). Must cover the full remote ReAct loop round-trip. | `300.0`    |

### llm_framework.extensions.mcp.MCPManager

```python
MCPManager(clients: list)
```

Aggregates multiple MCPClient connections and exposes a unified tool list.

Parameters:

| Name      | Type   | Description                                                                            | Default    |
| --------- | ------ | -------------------------------------------------------------------------------------- | ---------- |
| `clients` | `list` | List of MCPClient instances to aggregate. All are entered as a single context manager. | *required* |

### llm_framework.extensions.mcp.MCPServer

```python
MCPServer(name: str, lifespan=None)
```

Minimal MCP server supporting stdio and streamable-HTTP transports.

Parameters:

| Name       | Type  | Description                                                           | Default    |
| ---------- | ----- | --------------------------------------------------------------------- | ---------- |
| `name`     | `str` | Server name reported in the initialize handshake.                     | *required* |
| `lifespan` |       | Optional asynccontextmanager factory (server) -> AsyncIterator[dict]. | `None`     |

#### tool

```python
tool()
```

Decorator that registers an async function as an MCP tool.

#### run_stdio

```python
run_stdio()
```

Run the server reading JSON-RPC from stdin and writing responses to stdout.

#### run

```python
run()
```

Start the server in stdio mode (blocking).

#### http_app

```python
http_app()
```

Return a FastAPI ASGI app serving the MCP endpoint at POST /mcp. Requires [web] extra.

### llm_framework.extensions.mcp.MCPContext

```python
MCPContext(lifespan: dict)
```

Per-request context injected into MCP tool handlers.

______________________________________________________________________

## Memory

`MemoryStore` is a lightweight key-value persistence layer for recalled context. It is useful for user preferences, session facts, and other simple memory patterns without adding heavy dependencies.

### llm_framework.extensions.memory.MemoryStore

```python
MemoryStore(path: str | None = None)
```

Key-value memory store backed by an in-memory dict or an optional JSON file.

Parameters:

| Name   | Type  | Description | Default                                                                                            |
| ------ | ----- | ----------- | -------------------------------------------------------------------------------------------------- |
| `path` | \`str | None\`      | Optional path to a JSON file for persistence. Omit for in-memory only (data lost on process exit). |

______________________________________________________________________

## Auth

Auth primitives separate authentication (who the caller is) from authorization (which tools they can use). Use these types when your agent must enforce role-based or user-based access to tools.

### llm_framework.extensions.auth.AuthContext

```python
AuthContext(user_id: str, roles: set[str] = set(), attributes: dict[str, Any] = dict())
```

Resolved identity and role set for a single request.

### llm_framework.extensions.auth.AuthGate

```python
AuthGate(backend: PolicyBackend)
```

Enforces tool-access policy at schema filtering and at execution time.

Parameters:

| Name      | Type            | Description                                                             | Default    |
| --------- | --------------- | ----------------------------------------------------------------------- | ---------- |
| `backend` | `PolicyBackend` | A PolicyBackend that resolves tool permissions for a given AuthContext. | *required* |

#### filter_schemas

```python
filter_schemas(schemas: list[dict], context: AuthContext | None) -> list[dict]
```

Return only the JSON function schemas this context is allowed to call.

#### authorize

```python
authorize(tool_name: str, context: AuthContext | None) -> bool
```

Return True if this context may invoke the named tool.

### llm_framework.extensions.auth.backends.file.FilePolicyBackend

```python
FilePolicyBackend(path: str | Path)
```

Bases: `MemoryPolicyBackend`

RBAC + per-user ACL policy loaded from a JSON file; extends MemoryPolicyBackend with disk persistence.

Parameters:

| Name   | Type  | Description | Default                                                         |
| ------ | ----- | ----------- | --------------------------------------------------------------- |
| `path` | \`str | Path\`      | Path to a JSON policy file with roles and users top-level keys. |

#### reload

```python
reload()
```

Re-read the policy file from disk — call when the file changes at runtime.

### llm_framework.extensions.auth.backends.memory.MemoryPolicyBackend

```python
MemoryPolicyBackend(policy: dict)
```

In-process policy backend; same rules format as FilePolicyBackend but held in a dict.

Parameters:

| Name     | Type   | Description                                                                 | Default    |
| -------- | ------ | --------------------------------------------------------------------------- | ---------- |
| `policy` | `dict` | Dict with roles and users keys, matching the FilePolicyBackend JSON schema. | *required* |

#### get_allowed_tools

```python
get_allowed_tools(context: AuthContext) -> set[str]
```

Effective tool set: union of role grants + extra_tools − denied_tools.

### llm_framework.extensions.auth.providers.static.StaticAuthProvider

```python
StaticAuthProvider(api_keys: dict[str, AuthContext] | None = None, users: dict[str, AuthContext] | None = None)
```

Resolves credentials against a static in-process mapping; for development and testing only.

Parameters:

| Name       | Type                     | Description | Default                                                                                   |
| ---------- | ------------------------ | ----------- | ----------------------------------------------------------------------------------------- |
| `api_keys` | \`dict[str, AuthContext] | None\`      | Map of raw key string to AuthContext, matched via {"type": "api_key", "key": ...}.        |
| `users`    | \`dict[str, AuthContext] | None\`      | Map of username string to AuthContext, matched via {"type": "username", "username": ...}. |

### llm_framework.extensions.auth.providers.oidc.OIDCAuthProvider

```python
OIDCAuthProvider(client_id: str, client_secret: str, discovery_url: str, redirect_uri: str, roles_claim: str = 'roles', scopes: list[str] | None = None, role_map: dict[str, set[str]] | None = None)
```

OIDC Authorization Code flow; exchanges a provider-issued code for an AuthContext.

#### from_env

```python
from_env(redirect_uri: str, role_map: dict[str, set[str]] | None = None) -> 'OIDCAuthProvider'
```

Instantiate from OIDC_CLIENT_ID, OIDC_CLIENT_SECRET, OIDC_DISCOVERY_URL env vars.

#### authorization_url

```python
authorization_url(state: str) -> tuple[str, str]
```

Build the provider authorization URL; returns (url, code_verifier) for PKCE (RFC 7636).

#### exchange_code

```python
exchange_code(code: str, code_verifier: str) -> dict | None
```

Exchange an authorization code for decoded id_token claims, or None on failure.

#### resolve

```python
resolve(credentials: dict) -> AuthContext | None
```

Resolve OIDC authorization code credentials to an AuthContext.

______________________________________________________________________

## RAG

`RAGStore` handles ingest, chunking, embedding, and semantic retrieval workflows. Use it when your agent should ground answers in your own documents rather than only model priors.

### llm_framework.extensions.rag.RAGStore

```python
RAGStore(llm_client: object, storage_backend: BaseStorageBackend, default_max_tokens: int = 300, embed_batch_size: int = 64, _owns_client: bool = False)
```

Retrieval-augmented generation store: ingest files and search by semantic similarity.

Parameters:

| Name                 | Type                 | Description                                                                              | Default    |
| -------------------- | -------------------- | ---------------------------------------------------------------------------------------- | ---------- |
| `llm_client`         | `object`             | An LLMClient instance used exclusively for embedding requests.                           | *required* |
| `storage_backend`    | `BaseStorageBackend` | A BaseStorageBackend implementation (e.g. QdrantBackend).                                | *required* |
| `default_max_tokens` | `int`                | Approximate token limit per chunk when ingesting files (default 300).                    | `300`      |
| `embed_batch_size`   | `int`                | Maximum strings per embedding API call; prevents exceeding provider limits (default 64). | `64`       |

#### from_env

```python
from_env(storage_backend: BaseStorageBackend) -> RAGStore
```

Construct a RAGStore from env vars; must be used as an async context manager to avoid leaking the HTTP client.

#### ingest_file

```python
ingest_file(file_path: str | Path, max_tokens: int | None = None)
```

Convert, chunk, embed, and store a file; returns the number of chunks ingested.

#### search

```python
search(query: str, limit: int = 3)
```

Return the top-k most semantically similar passages for a query string.

______________________________________________________________________

## Vector Store

Vector backends provide the storage/search engine behind RAG retrieval. `QdrantBackend` is the default implementation and supports local, in-memory, and remote modes.

### llm_framework.extensions.rag.vector_store.qdrant.QdrantBackend

```python
QdrantBackend(collection_name: str = 'knowledge_base', vector_size: int = 768, path: str | None = None, url: str | None = None)
```

Qdrant-based vector storage; supports in-memory, local file, and remote cluster modes.

Parameters:

| Name              | Type  | Description                                                                               | Default                                                             |
| ----------------- | ----- | ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| `collection_name` | `str` | Qdrant collection to use (default knowledge_base).                                        | `'knowledge_base'`                                                  |
| `vector_size`     | `int` | Dimensionality of embedding vectors; must match the embedding model output (default 768). | `768`                                                               |
| `path`            | \`str | None\`                                                                                    | Local file path for a persistent on-disk store. Omit for in-memory. |
| `url`             | \`str | None\`                                                                                    | Remote Qdrant cluster URL. Takes precedence over path.              |

______________________________________________________________________

## Guardrails

Guardrails are composable filters that validate or transform agent input and output. Use them to block unsafe prompts, redact sensitive output, or enforce policy boundaries.

### llm_framework.extensions.guardrails.block_keywords

```python
block_keywords(words: list[str])
```

Return a guard that raises if any blocked keyword appears in the text (case-insensitive).

### llm_framework.extensions.guardrails.strip_pii

```python
strip_pii()
```

Return a guard that replaces email addresses and phone numbers with redaction placeholders.

### llm_framework.extensions.guardrails.llm_guard

```python
llm_guard(client, policy: str)
```

Return an async guard that evaluates text against a natural language policy using an LLM.

Requires a provider that supports structured output (json_schema response_format with strict=True).
