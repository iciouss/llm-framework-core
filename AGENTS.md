# AGENTS.md

## Project

Minimal Python library for building LLM-powered agents. Priority: low dependency footprint and supply chain safety.

- `core/` requires only `httpx`. Always available.
- `extensions/` are optional. Pull only what you need.
- Every feature targets the "goldilocks" zone: use a library where it saves meaningful complexity, write from scratch where it adds unnecessary deps.

## Development

**Install:**
```sh
uv venv && source .venv/bin/activate
uv pip install -e .               # core only: httpx, python-dotenv
uv pip install -e ".[rag]"        # + pypdf, semantic-text-splitter
uv pip install -e ".[qdrant]"     # + qdrant-client
uv pip install -e ".[oidc]"       # + PyJWT[crypto] for OIDC Authorization Code flow
uv pip install -e ".[all]"        # all library extras: rag, qdrant, oidc
uv sync --group core              # same as base install; explicit marker
uv sync --group extra             # all library extras
uv sync --group examples          # library extras + web; install before running any example
```

Requires Python 3.13+.

**Run the web chat agent:**
```sh
python examples/chats/16_web_agent.py                    # http://127.0.0.1:8080
python examples/chats/16_web_agent.py --port 9090        # custom port
python examples/chats/16_web_agent.py --no-mcp --open    # skip MCP servers, auto-open browser
```
Requires `[web]` extra. MCP servers are optional — the agent starts without them if they fail.

**Run the web chat agent with password auth:**
```sh
python examples/chats/18.1_web_auth_agent.py --open           # http://127.0.0.1:8080
```
Requires `[web]` extra. Three demo users: admin / alice / bob (passwords printed at startup).

**Run the web chat agent with OIDC SSO:**
```sh
uv pip install -e ".[web,oidc]"
python examples/chats/18.2_web_oidc_agent.py --open           # http://127.0.0.1:8080
```
Requires `[web,oidc]` extras and `OIDC_CLIENT_ID`, `OIDC_CLIENT_SECRET`, `OIDC_DISCOVERY_URL` in `.env`.

**Run the knowledge MCP server:**
```sh
uv run knowledge-server --http --port 8082   # streamable HTTP at /mcp
uv run knowledge-server                      # stdio (for subprocess transport)
```
Requires `LLM_BASE_URL`, `LLM_API_KEY`, `EMBED_MODEL` (or falls back to `LLM_MODEL`). Optional: `VECTOR_BACKEND`, `QDRANT_*` vars.

**Run the memory MCP server:**
```sh
uv run memory-server --http --port 8083              # streamable HTTP at /mcp
uv run memory-server                                 # stdio (for subprocess transport)
```
`MEMORY_PATH` env var sets the JSON file for persistence. Omit for in-memory only.

**Environment:** Copy `.env.example` to `.env` and fill in values. Required vars: `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`. Optional: `CA_BUNDLE_PATH` for custom TLS certs.

**`.env.example` format:** Each variable must follow this exact pattern — no section dividers, no extra commentary lines:
```
# [Required] One-line description.
VAR_NAME=default_value

# [Optional] One-line description.
# VAR_NAME=default_value
```

**Run tests:** Tests are standalone integration scripts — not pytest. All tests read LLM config from `.env` via `LLMClient.from_env()` — no hardcoded credentials.
```sh
python tests/core/test_guardrails.py
python tests/core/test_orchestrator.py
python tests/core/test_structured_output.py
python tests/core/test_history.py      # no LLM needed
python tests/core/test_cached_tool.py  # no LLM needed
python tests/core/test_rag_formats.py  # no LLM needed; tests all file format extractors
python tests/core/test_memory.py       # spawns memory-server as subprocess automatically
python tests/core/test_rag.py          # spawns knowledge-server; needs qdrant + embeddings endpoint
```

## Coding Rules

- Single-line comments only. No block comments.
- Docstrings on `@tool` and `@mcp.tool()` functions are required (used for schema auto-generation): one-line summary + `Args:` block for every parameter.
- On public methods of services, managers, and protocol interfaces (`AuthProvider`, `PolicyBackend`, `BaseStorageBackend`): full docstring when the name alone does not convey side effects, return shape, or contract expectations; otherwise one line max.
- On all other classes and functions: one line max. Skip entirely when the name is self-explanatory.
- `Returns:` and `Raises:` blocks are optional everywhere except protocol interface methods, where they describe the implementor contract.
- No emojis.
- No numbered comments (no `# step 1:`, `# 1.`, etc.).
- Comments explain *why*, not *what* the code does. Keep them to one clause.
- Names must be provider/backend-agnostic. Avoid hardcoding service/library names in comments or variable names.
- Pareto principle: handle the 80% case cleanly. Skip try/except for edge cases that won't occur in practice.
- Consistency: any pattern introduced in one file of a group (e.g. `tools/`, `mcp_servers/`) must be applied to all equivalent files in that group immediately — error surfacing, `__main__` CLI blocks, logging, etc.
- Protocol methods must be fully implemented. Never stub an interface method with `return None` as a workaround; either implement it or redesign the protocol.

## Architecture

```
core/               — httpx only; always available
  llm.py            — async HTTP client for OpenAI-compatible chat + embeddings
  tools.py          — @tool decorator: type hints + docstring → JSON schema
  agent.py          — ReAct loop: chat → tool calls → observations → repeat
  history.py        — HistoryBuffer: rolling multi-turn history with token-budget trimming
  orchestrator.py   — multi-agent supervisor/delegate pattern

extensions/         — optional; install extras as needed
  memory.py         — stdlib JSON-backed key-value store (zero new deps)
  auth/
    __init__.py     — public re-exports
    _context.py     — AuthContext
    backends/       — PolicyBackend protocol + FilePolicyBackend, MemoryPolicyBackend
    providers/      — AuthProvider protocol + StaticAuthProvider, OIDCAuthProvider
  mcp/
    __init__.py     — re-exports MCPClient, MCPManager, MCPServer, MCPContext
    client.py       — MCPClient: async MCP client over stdio or streamable-HTTP; MCPManager: aggregates multiple clients
    server.py       — MCPServer + MCPContext: minimal MCP server (replaces third-party library)
  rag/
    __init__.py     — RAGStore, BaseStorageBackend protocol, backend_from_env factory
    _converter.py   — file-to-markdown conversion for all supported formats
    vector_store/
      __init__.py
      qdrant.py     — Qdrant backend (in-memory, local, or remote)
  guardrails.py     — composable input/output guard functions (zero new deps)

tools/              — @tool-decorated callables; import directly into any agent, run in-process
  filesystem.py     — read/write/list/info, sandboxed to home dir
  web_fetch.py      — fetch URL, HTML stripped to plain text
  calculator.py     — basic arithmetic
  clock.py          — current UTC datetime
  shell.py          — sandboxed subprocess execution (allowlisted commands only)
  memory.py         — make_memory_tools(store): returns @tool closures bound to a MemoryStore instance

mcp_servers/        — MCPServer application servers (@mcp.tool); run as separate processes via stdio or HTTP
  knowledge_server.py    — MCPServer exposing search_notes + ingest_file; RAGStore managed via lifespan
  memory_server.py       — MCPServer exposing save/recall/list/delete memory; MemoryStore managed via lifespan

examples/           — runnable scripts, one concept each
  basics/           — 01-09: LLM client, agent, tools, structured output, guardrails, MCP, approval, orchestrator, agent-as-tool
  advanced/         — 10, 11, 13, 14, 17: RAG, custom MCP server, history buffer, cached tool, auth agent
  chats/            — 15, 16, 18.1, 18.2: CLI REPL, web chat, auth (password + OIDC) + HTML templates
  specialized_agents/ — researcher_agent.py (full agent server exposing delegate_to_researcher)
```

For API usage examples and behavioral reference, see [`docs/patterns.md`](docs/patterns.md).

## How to Add a Tool

1. Create or edit a file in `tools/`.
2. `from llm_framework.core import tool`
3. Decorate with `@tool`, write a one-line docstring.
4. No module headers, no class wrappers.

## How to Add an Integration

1. Create `extensions/my_feature.py`.
2. If it has zero new deps, import it unconditionally in `extensions/__init__.py`.
3. If it needs optional packages, wrap the import in a try/except in `extensions/__init__.py` with a stub that raises a clear `ImportError`.
4. Add a new named extra to `pyproject.toml [project.optional-dependencies]` — one extra per feature, never bundle unrelated deps together. Library extras (extend the library API) go into `all`; extras that are only needed to run example scripts (e.g. `web`) do not. Use `uv add --optional <extra-name> <package>` to add the package — never write version pins by hand.

## How to Add an Agent Server (Agent-as-a-Tool)

Use this pattern to expose a complete agent as a single MCP tool. Any caller connects via `MCPClient.http(url, timeout=300.0)` and delegates tasks without knowing the agent's internal tools, LLM, or system prompt.

**Contract:** every agent server exposes exactly one tool named `delegate_to_{name}(task: str) -> str`. Uniform interface, unique name when aggregated, description is what tells the caller's model what the specialist handles.

1. Create `examples/specialized_agents/my_agent.py`.
2. Define a `lifespan` that creates the `LLMClient` and any dependency servers (spawn via `MCPClient.stdio` if needed):
```python
@asynccontextmanager
async def lifespan(server: MCPServer) -> AsyncIterator[dict]:
    async with LLMClient.from_env() as client:
        yield {"client": client, "tools": my_tools}
```
3. Expose one tool:
```python
@mcp.tool()
async def delegate_to_my_agent(task: str, ctx: MCPContext) -> str:
    """One-line description of what this agent handles.

    Args:
        task: Natural language instruction.
    """
    client = ctx.lifespan["client"]
    tools  = ctx.lifespan["tools"]
    agent  = Agent(client=client, tools=tools, system_prompt="...", max_tokens=4096)
    result = await agent.run(task)
    answer = result.get("answer", "(no answer)")
    return answer[:8000] + ("\n...[truncated]" if len(answer) > 8000 else "")
```
4. Add `argparse` main with `--http/--port` following the pattern in `examples/specialized_agents/researcher_agent.py`.
5. Add a `logging.FileHandler` for `on_event` so internal ReAct traces are written to `{name}.log`.
6. Callers connect with `MCPClient.http("http://host:PORT/mcp", timeout=300.0)` — no knowledge of internals required.

## How to Add an MCP Server for External Tools

Use this when tools talk to an external API and you want them available to any MCP client (not just this agent).

1. Create `llm_framework/mcp_servers/my_server.py`.
2. Define a `lifespan` async context manager that creates and yields shared clients:
```python
@asynccontextmanager
async def lifespan(server: MCPServer) -> AsyncIterator[dict]:
    async with MyClient.from_env() as client:
        yield {"client": client}

mcp = MCPServer("my-server", lifespan=lifespan)
```
3. Decorate tools with `@mcp.tool()`. Access shared state via `ctx: MCPContext` parameter:
```python
@mcp.tool()
async def my_tool(query: str, ctx: MCPContext) -> str:
    client = ctx.lifespan["client"]
    ...
```
4. `MCPContext` is injected automatically by `MCPServer` and stripped from the exposed schema.
5. Add a CLI entrypoint to `pyproject.toml [project.scripts]`.
6. Connect from your agent via `MCPClient.stdio("uv", ["run", "my-server"])` or `MCPClient.http("http://localhost:PORT/mcp")`.

## How to Add a Vector Backend

1. Create `extensions/rag/vector_store/my_backend.py` and implement `upsert()` and `search()` — no base class needed, `BaseStorageBackend` is a structural protocol.
2. Add a branch to `backend_from_env()` in `extensions/rag/__init__.py` to instantiate it from env vars.
3. Add a new pyproject extra if the backend needs a new package.

## How to Add an Auth Provider

Authentication and authorization are handled by `extensions/auth.py` (zero new deps).
Two concerns are intentionally decoupled:

- **Authentication** (`AuthProvider`) — resolves raw credentials to an `AuthContext`. Lives at
  the transport layer (HTTP handler, WebSocket handshake). Swap implementations without touching
  the agent.
- **Authorization** (`AuthGate` + `PolicyBackend`) — filters tool schemas and enforces access at
  execution time. Lives inside `Agent`.

**Quick setup:**

```python
from llm_framework.extensions.auth import (
    AuthContext, AuthGate, FilePolicyBackend, StaticAuthProvider,
)

# 1. load a policy file (or use MemoryPolicyBackend for in-process config)
gate = AuthGate(FilePolicyBackend("policy.json"))

# 2. wire the gate into the agent at construction time
agent = Agent(client, tools=my_tools, auth_gate=gate)

# 3. resolve the caller's identity at request time and pass it to run()
provider = StaticAuthProvider(api_keys={"sk-xyz": AuthContext(user_id="alice", roles={"analyst"})})
ctx = await provider.resolve({"type": "api_key", "key": request_api_key})
result = await agent.run(prompt, auth_context=ctx)
```

**Policy file format** (`policy.json`):

```json
{
  "roles": {
    "admin":   {"tools": ["*"]},
    "analyst": {"tools": ["web_search", "fetch_url", "read_file"]},
    "viewer":  {"tools": ["get_current_datetime"]}
  },
  "users": {
    "alice": {"roles": ["analyst"], "extra_tools": ["write_file"]},
    "bob":   {"roles": ["viewer"],  "denied_tools": ["get_current_datetime"]}
  }
}
```

`"*"` wildcard grants access to every registered tool. `extra_tools` / `denied_tools` are
per-user ACL overrides on top of role grants.

**To add a custom AuthProvider** (e.g. JWT, OIDC, LDAP):

1. Implement `async def resolve(self, credentials: dict) -> AuthContext | None`.
2. `credentials` is transport-agnostic — use any key structure that matches how credentials
   arrive in your transport (HTTP header, WebSocket param, CLI flag, etc.).
3. Return `None` when credentials are unrecognized (caller will be unauthenticated).
4. No base class to inherit — the `AuthProvider` protocol is structural (`runtime_checkable`).

```python
class JWTAuthProvider:
    async def resolve(self, credentials: dict) -> AuthContext | None:
        token = credentials.get("token")
        if not token:
            return None
        payload = verify_jwt(token)  # your validation logic
        return AuthContext(
            user_id=payload["sub"],
            roles=set(payload.get("roles", [])),
        )
```

For full OIDC usage examples and session cookie notes, see [`docs/patterns.md`](docs/patterns.md).

**To add a custom PolicyBackend** (e.g. database, Open Policy Agent):

1. Implement `get_allowed_tools(context: AuthContext) -> set[str]` and
   `is_allowed(tool_name: str, context: AuthContext) -> bool`.
2. Pass an instance to `AuthGate(my_backend)`.
3. No base class — `PolicyBackend` is a structural protocol.

**Defense-in-depth:** `AuthGate` enforces access at two points:
- **Schema filtering** — unauthorized tools are stripped from the schema list before the LLM
  request, so the model never learns about tools it cannot use (saves tokens too).
- **Execution-time check** — `_execute_tool` re-verifies authorization before running any tool,
  protecting against prompt injection that forges unauthorized tool calls.

When `auth_gate` is `None` or `auth_context` is `None`, all tools are available — existing
agents require no changes.

## After Each Implementation

Before considering work done, verify the following and fix anything that is not satisfied:

1. **Coding rules** — single-line comments only; no block comments; no numbered comments; no emojis; comments explain *why* not *what*; names are provider/backend-agnostic; `@tool`/`@mcp.tool()` functions have full docstrings with `Args:`; public service/manager methods and protocol interfaces have full docstrings when non-obvious; all other functions one line max or omit; protocol methods fully implemented.
2. **Consistency** — any pattern introduced in one file of a group (`tools/`, `mcp_servers/`) must be applied to all equivalent files in that group immediately (error surfacing, `__main__` CLI blocks, logging, `_MAX_CHARS` truncation, etc.).
3. **`pyproject.toml`** — new optional dependencies get their own named extra and are added to `[all]`; new servers get an entrypoint under `[project.scripts]`.
4. **`.env.example`** — every new env var is documented following the exact format: `# [Required|Optional] One-line description.` on the line above the variable; no section dividers; no extra commentary lines.
5. **`AGENTS.md` Architecture table** — new files in `core/`, `extensions/`, `tools/`, `mcp_servers/`, or `examples/` are listed with a one-line description.
6. **`README.md`** — new MCP servers documented under **MCP Tools Servers**; new agent servers under **Agent Servers**; new examples added to the examples table; new config vars in the **Configuration** section if user-facing.
7. **`docs/`** — if a new feature has user-facing API or env vars, the relevant docs page is updated (e.g. `docs/environment-variables.md` renders from `.env.example` automatically via the macro, so no manual update needed there).

## Documentation Scope

Each documentation location has a distinct audience and update trigger. Update only what is relevant to the change — do not update all locations for every change.

| Location | Audience | Update when |
|---|---|---|
| **`AGENTS.md`** | AI agents and contributors writing code in this repo | Adding files to tracked directories, changing dev commands, adding coding rules, changing how-to patterns |
| **`README.md`** | New users and library consumers | Adding user-facing features, new config vars, new examples, new MCP/agent servers |
| **`docs/patterns.md`** | Developers using the library in their own code | New usage patterns, new transport options, behavioral changes to public API |
| **`docs/api/`** | Library consumers needing reference docs | New public classes or functions in `core/`, `extensions/`, `tools/`. Add `### ::: module.ClassName` entries; update section descriptions if transports/options change |
| **`docs/environment-variables.md`** | Operators deploying the service | Auto-generated from `.env.example` — no manual edits; document new vars in `.env.example` instead |
| **Docstrings** | IDE users and `docs/api/` auto-render | Required on every `@tool` function (used for schema generation). One line max on other public classes/functions; skip when the name is self-explanatory |

**What does NOT need documentation:**
- Internal refactors that preserve the public API (rename a private var, split a private function)
- Bug fixes that restore already-documented behavior
- Test additions

**Quick reference — common change types:**

- New `@tool` function → docstring + `AGENTS.md` Architecture table
- New public class in `extensions/` → docstring + `docs/api/extensions.md` entry + `AGENTS.md` table
- New env var → `.env.example` entry (auto-renders to `docs/environment-variables.md`)
- New MCP server → `README.md` MCP servers table + `AGENTS.md` table + `pyproject.toml` entrypoint
- Renamed class/method → update every documentation location that mentions the old name

## Git Commit Convention

Use conventional commits: `type(scope): description`

- Types: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`
- Subject line: lowercase, imperative mood, under 72 characters
- Body: only when the subject alone is not enough — short bullet points on WHAT and WHY, not HOW
