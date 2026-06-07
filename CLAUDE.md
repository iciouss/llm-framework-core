# CLAUDE.md

Instructions for AI agents (Claude Code, GitHub Copilot, Cursor, etc.) working in this repository. Single source of truth — keep it current.

## Project

Minimal Python library for building LLM-powered agents. Priority: low dependency footprint and supply chain safety.

- `core/` requires only `httpx` and `python-dotenv`. Always available.
- `extensions/` are optional. Pull only what you need via extras (`[mcp]`, `[rag]`, `[qdrant]`, `[oidc]`, `[std]`).
- Every feature targets the "goldilocks" zone: use a library where it saves meaningful complexity, write from scratch where it adds unnecessary dependencies.
- Python 3.13+ is required (uses `from __future__ import annotations`, PEP 604 unions, `dataclass(slots=...)` patterns freely).

## Quick Start

```sh
uv venv && source .venv/bin/activate
uv pip install -e .               # core only
uv pip install -e ".[mcp]"        # + fastapi (MCP server HTTP transport)
uv pip install -e ".[rag]"        # + pypdf, semantic-text-splitter, sqlite-vec
uv pip install -e ".[qdrant]"     # + qdrant-client (set VECTOR_BACKEND=qdrant)
uv pip install -e ".[oidc]"       # + PyJWT[crypto] (OIDC SSO)
uv pip install -e ".[std]"        # rag + oidc (recommended full install)
```

| Extra | Adds |
|---|---|
| *(none)* | `httpx`, `python-dotenv` |
| `[mcp]` | `fastapi` |
| `[rag]` | `pypdf`, `semantic-text-splitter`, `sqlite-vec` |
| `[oidc]` | `PyJWT[crypto]` |
| `[std]` | `rag` + `oidc` |
| `[qdrant]` | `qdrant-client` (pair with `[rag]`) |

Environment: copy `.env.example` to `.env`. Required: `LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`. Optional: `CA_BUNDLE_PATH`, `VECTOR_BACKEND`, `SQLITE_PATH`, `QDRANT_*`, `MEMORY_PATH`, `OIDC_*`.

Commands:

```sh
# Unit tests (no LLM required)
uv run pytest tests/unit tests/test_packaging.py -v

# Integration tests (requires live LLM endpoint)
uv run pytest tests/integration -v -m integration

# Build & serve docs
uv run --project docs mkdocs serve

# Run the in-tree MCP servers
uv run knowledge-server --http --port 8082
uv run memory-server --http --port 8083

# Run the web chat agent
python examples/chats/16_web_agent.py
```

## Architecture

Three layers, one-way dependencies (`core` never imports from `extensions`):

```
llm_framework/
  _env.py              — load_env() helper; reads .env from cwd
  _optional.py         — EXTRAS_MAP + require() for optional-dep sentinels
  observability.py     — events, hook, ContextVar — pending move into core/ (see ISSUES #10)

  core/                — httpx only; always available
    llm.py             — async HTTP client for OpenAI-compatible chat + embeddings
    tools.py           — @tool decorator: type hints + docstring → JSON schema; @cached_tool LRU variant
    agent.py           — ReAct loop: chat → tool calls → observations → repeat
    history.py         — HistoryBuffer: rolling multi-turn history with token-budget trimming
    orchestrator.py    — multi-agent supervisor / delegate pattern
    protocols.py       — structural Protocols; lets core declare shapes without importing extensions

  extensions/          — optional; install extras as needed
    memory.py          — stdlib JSON-backed key-value store (zero new deps)
    auth/              — AuthContext, AuthGate, PolicyBackend, FilePolicyBackend, MemoryPolicyBackend
    mcp/               — MCPClient (stdio + streamable HTTP), MCPManager, MCPServer, MCPContext
    rag/               — RAGStore, BaseStorageBackend protocol, sqlite-vec + qdrant backends
    guardrails.py      — composable input/output guard functions (zero new deps)

  tools/               — @tool-decorated callables shipped in the lib
                        PENDING MOVE: most of these will move to examples/ (see ISSUES #8)
    filesystem.py      — read/write/list/info, sandboxed to home dir
    web_fetch.py       — fetch URL with SSRF protection
    shell.py           — sandboxed subprocess (allowlisted commands only)
    memory.py          — make_memory_tools(store) factory
    builtins.py        — calculator + clock (will move to examples/)

  mcp_servers/         — @mcp.tool servers; entry-point scripts
                        PENDING MOVE: will move to examples/ (see ISSUES #8, #13)
    knowledge_server.py
    memory_server.py
```

For API reference: `docs/api/`. For usage patterns: `docs/patterns.md`. For environment variables: `docs/environment-variables.md` (auto-rendered from `.env.example`).

## Coding Rules

These are non-negotiable. See `.github/copilot-instructions.md` for the parallel "strict Python standards" set.

**Comments**
- Single-line comments only. No block comments.
- Comments explain *why*, not *what* the code does. Keep them to one clause.
- No numbered comments (`# step 1:`, `# 1.`, etc.).
- No emojis anywhere in code or docs.

**Naming**
- snake_case for functions/variables, PascalCase for classes, UPPER_CASE for module-level constants.
- Names must be provider-/backend-agnostic. Avoid hardcoding service/library names in comments or variable names.

**Type hints**
- 100% type annotations on all function signatures (args and return) and class attributes.
- Use `from __future__ import annotations` at the top of every module.
- Prefer `T | None` (PEP 604) over `Optional[T]`. Use `Any` only at protocol boundaries.
- Banned: mutable default arguments. Banned: dynamic attribute lookups (`getattr`, `hasattr`) for inter-module contracts — use `Protocol` or explicit type checks.

**Docstrings**
- Required on `@tool` and `@mcp.tool()` functions (used for schema auto-generation): one-line summary + `Args:` block for every parameter.
- On public methods of services, managers, and Protocol interface methods: full docstring when side effects / return shape / contract are not obvious from the name. Include `Returns:` and `Raises:` when non-trivial.
- On all other classes/functions: one line max, or omit entirely when the name is self-explanatory.

**Optional dependencies** — NEVER use lazy imports inside function bodies. Always the three-step sentinel pattern:
1. Add `"package_name": "extra_name"` to `EXTRAS_MAP` in `llm_framework/_optional.py`.
2. Declare a top-level sentinel: `try: import pkg / except ImportError: pkg = None  # type: ignore[assignment]`.
3. Call `_require("pkg", pkg)` at instantiation or first use (not at import time). Import always succeeds; failure is deferred to use.

**Adding dependencies** — never edit `pyproject.toml` to add or bump a version pin by hand. Always use `uv add`:
- Runtime deps: `uv add <pkg>`
- Optional extras: `uv add --optional <extra-name> <pkg>` (one extra per feature; never bundle unrelated deps)
- Dev group: `uv add --group dev <pkg>`

This keeps the recorded minimum version equal to the current latest, prevents drift between `pyproject.toml` and `uv.lock`, and avoids typo'd or stale version strings. Applies to upgrades too: `uv add --upgrade <pkg>`, don't bump a constraint in place.

**Architecture**
- Strict DAG imports. `core/` must not import from `extensions/` at runtime. Use `Protocol` + `TYPE_CHECKING` for type-only references.
- Submodules must import from explicit submodule paths, never from the top-level package `__init__.py`. Prevents recursive execution loops.
- Catch specific exceptions. `except Exception:` is a code smell; either re-raise, handle specifically, or define a domain exception.
- Protocol methods must be fully implemented. Never stub a Protocol method with `return None` as a workaround — either implement it or redesign the Protocol.

**Consistency**
- Any pattern introduced in one file of a group (`tools/`, `mcp_servers/`, `extensions/*/`) must be applied to all equivalent files in that group immediately — error surfacing, `__main__` CLI blocks, logging, `_MAX_CHARS` truncation, etc.
- Pareto principle: handle the 80% case cleanly. Don't add try/except for edge cases that won't occur in practice.

## Patterns You'll Use Often

**`@tool` decorator** — turns a typed function into an LLM-callable tool:

```python
from llm_framework.core import tool

@tool
def my_tool(query: str, limit: int = 5) -> str:
    """One-line summary of what the tool does.

    Args:
        query: Description shown to the model.
        limit: Max results to return.
    """
    return f"results for {query}"
```

Schema is built from type hints + docstring automatically. Supports sync and async. Use `@cached_tool(maxsize=128)` for LRU caching.

**Optional-dependency sentinel** — for new optional packages:

```python
# in extensions/my_feature/__init__.py
try:
    import my_pkg
except ImportError:
    my_pkg = None  # type: ignore[assignment]

def make_client():
    from llm_framework._optional import require
    require("my_pkg", my_pkg)  # raises ImportError with install hint
    return my_pkg.Client()
```

Then in `pyproject.toml`:

```toml
[project.optional-dependencies]
my_feature = ["my_pkg>=1.0"]
```

**Structural Protocol for cross-layer contracts** — when `core` needs to type-hint a collaborator from `extensions`:

```python
# in core/protocols.py
from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from llm_framework.extensions.my_feature import MyService  # only for type-checker

class MyServiceProtocol(Protocol):
    async def do_thing(self, x: str) -> dict: ...
```

The concrete class in `extensions/my_feature/` satisfies the Protocol structurally — no inheritance required.

**Observability event** — every meaningful call site emits one:

```python
from llm_framework.observability import emit, MyEvent

await emit(MyEvent(
    event_type="started",
    payload={"x": 42},
))
```

The global hook is opt-in. With no hook registered, `emit()` is a no-op. Observability is the right place for cross-cutting concerns; the per-instance `on_step` callback is for tight integration with a specific agent.

## What NOT to Do

This is a curated list of mistakes that have actually happened in this repo. See the private review notes (in `issues/REVIEW_*.md`, gitignored) for the full issue list with rationale.

- **Don't ship `tools/builtins.py`** in the library. Demo functions belong in `examples/`.
- **Don't reach into another module's internals** to inject state (e.g., the `Orchestrator` mutating a sub-agent's `on_event`). Use the public API or the observability hook.
- **Don't use lazy imports** inside function bodies. Use the sentinel pattern.
- **Don't double-count tokens.** Reasoning tokens are a *subset* of completion tokens, not additive.
- **Don't bake IdP-specific fallbacks into generic OIDC code.** Either commit to a specific IdP (and say so) or remove the fallbacks.
- **Don't `print()` for observability.** Use the observability hook or stdlib logging.
- **Don't catch `Exception` to silence errors.** Catch the specific type you expect.
- **Don't add new top-level package files without updating this map.**

## How to Add Things

### A tool

1. Create or edit a file in `tools/` (or `examples/basics/` if it's a demo).
2. `from llm_framework.core import tool`
3. Decorate with `@tool`. One-line docstring + `Args:` block for every parameter.
4. No module headers, no class wrappers.

### An extension

1. Create `extensions/my_feature.py` (single file) or `extensions/my_feature/` (package).
2. Zero new deps → import unconditionally in `extensions/__init__.py`.
3. Has optional deps → use the sentinel pattern. Add to `_optional.EXTRAS_MAP`. Declare a new named extra in `pyproject.toml` — one extra per feature, never bundle unrelated deps.
4. Re-export the public surface in `extensions/__init__.py`.

### An MCP server (exposing tools to any MCP client)

1. Create `mcp_servers/my_server.py` (or `examples/specialized_agents/my_agent.py` if it's an agent-as-a-tool — see below).
2. Define a `lifespan` async context manager that yields shared clients/resources.
3. Decorate tools with `@mcp.tool()`. Access shared state via `ctx: MCPContext` parameter.
4. Add `argparse` CLI with `--http/--port` flags.
5. Add an entry point in `pyproject.toml [project.scripts]`.
6. Connect from agents with `MCPClient.stdio("uv", ["run", "my-server"])` or `MCPClient.http(url)`.

### An agent server (agent-as-a-tool)

Contract: every agent server exposes exactly one tool named `delegate_to_{name}(task: str) -> str`. Uniform interface, unique name when aggregated.

1. Create `examples/specialized_agents/my_agent.py`.
2. `lifespan` builds the `LLMClient` and any tool list.
3. `@mcp.tool() async def delegate_to_my_agent(task: str, ctx: MCPContext) -> str:` runs `Agent.run(task)` and returns the answer (truncated to ~8000 chars).
4. Add `argparse` main with `--http/--port`.
5. Add a `logging.FileHandler` to capture ReAct traces to `{name}.log`.
6. Callers connect with `MCPClient.http("http://host:PORT/mcp", timeout=300.0)`.

### A vector backend

1. Create `extensions/rag/vector_store/my_backend.py` implementing `async def upsert(...)` and `async def search(...)`. No base class — `BaseStorageBackend` is a structural Protocol.
2. Add a branch to `backend_from_env()` in `extensions/rag/__init__.py`.
3. Add a pyproject extra if the backend needs a new package.

### An auth provider

1. Implement `async def resolve(self, credentials: dict) -> AuthContext | None`. No base class — `AuthProvider` is a structural Protocol.
2. `credentials` is transport-agnostic. Use whatever key structure matches how credentials arrive in your transport.
3. Return `None` when credentials are unrecognized.

For full OIDC usage examples, see `docs/patterns.md` and `examples/chats/18.2_web_oidc_agent.py`.

## After Each Implementation

Run through this checklist before considering work done:

1. **Coding rules pass** — single-line comments, no block/numbered comments, no emojis, names are provider-agnostic, full docstrings on `@tool`/`@mcp.tool()` functions and Protocol methods.
2. **Consistency** — if you introduced a pattern in one `tools/` or `mcp_servers/` file, apply it to all equivalent files in that group.
3. **`pyproject.toml` updated** — new optional deps have their own named extra; new servers have a `[project.scripts]` entry. Run `uv run --with pytest pytest tests/test_packaging.py` (asserts every extra is mentioned in README, this file, `docs/getting-started/installation.md`, `docs/api/extensions.md`).
4. **`.env.example` updated** — new env vars follow the exact format: `# [Required|Optional] One-line description.` on the line above, no section dividers, no extra commentary.
5. **Architecture map above updated** — new files in `core/`, `extensions/`, `tools/`, `mcp_servers/`, or `examples/` get a one-line entry.
6. **README updated** — new MCP servers under "MCP Tools Servers", new agent servers under "Agent Servers", new examples in the examples table, new user-facing config vars in the "Configuration" section.
7. **`docs/` updated** — new user-facing features get an entry in `docs/api/` and/or `docs/patterns.md`. `docs/environment-variables.md` auto-renders from `.env.example`.
8. **Tests added** — unit tests for pure logic, integration tests for anything requiring a live LLM endpoint.
9. **Open issues checked** — if your change addresses an issue tracked in the private review notes (`issues/REVIEW_*.md`, gitignored), update its status line there. The review file is internal; commit messages don't reference it.
10. **`CHANGELOG.md` updated** — any user-facing change (new feature, breaking change, bug fix) gets one bullet under `[Unreleased]` in the appropriate section (`Added` / `Changed` / `Deprecated` / `Removed` / `Fixed` / `Security`). Internal refactors that don't change the public API can be skipped. Keep each bullet to one line and phrase it from the user's perspective, not the implementer's. Reference the issue number when relevant.

## Documentation Scope

| Location | Audience | Update when |
|---|---|---|
| **`CLAUDE.md`** (this file) | AI agents and contributors writing code in this repo | Adding files to tracked directories, changing dev commands, adding coding rules, changing how-to patterns |
| **`.github/copilot-instructions.md`** | GitHub Copilot specifically | Strict Python standards updates |
| **`README.md`** | New users and library consumers | Adding user-facing features, new config vars, new examples, new MCP/agent servers |
| **`CHANGELOG.md`** | Downstream users and library consumers | Any user-facing change (new feature, breaking change, bug fix). One bullet under `[Unreleased]` in the right section (`Added` / `Changed` / `Deprecated` / `Removed` / `Fixed` / `Security`). On release, rename `[Unreleased]` to `[X.Y.Z] — YYYY-MM-DD` and add a fresh empty `[Unreleased]` |
| **`LICENSE`** | Anyone redistributing or building on the project | The file only needs to be touched if the license itself changes (rare). If you do change it, this is a major event — coordinate before committing |
| **`docs/patterns.md`** | Developers using the library in their own code | New usage patterns, new transport options, behavioral changes to public API |
| **`docs/api/`** | Library consumers needing reference docs | New public classes or functions in `core/`, `extensions/`, `tools/`. Add `### ::: module.ClassName` entries |
| **`docs/environment-variables.md`** | Operators deploying the service | Auto-generated from `.env.example` — never edit manually |
| **`issues/REVIEW_*.md`** | Future AI agents + the maintainer | After every code review / audit pass |
| **Docstrings** | IDE users and `docs/api/` auto-render | Required on every `@tool` function (used for schema generation) |

**What does NOT need documentation:**
- Internal refactors that preserve the public API
- Bug fixes that restore already-documented behavior
- Test additions

**Quick reference — common change types:**
- New `@tool` function → docstring + this file's Architecture map
- New public class in `extensions/` → docstring + `docs/api/extensions.md` entry + this file's map
- New env var → `.env.example` entry (auto-renders to `docs/environment-variables.md`)
- New MCP server → `README.md` MCP servers table + this file's map + `pyproject.toml` entrypoint
- Renamed class/method → grep all doc locations and update every mention

## Git Commits

**Never commit or push without explicit user instruction.** Never amend already-pushed commits. When the user asks for commits, propose both the `git add` and the `git commit` commands — never just the message.

### Format

```
type(scope): lowercase imperative subject under 72 chars

- bullet naming what changed
```

- **Types:** `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`.
- **Subject:** lowercase, imperative, under 72 chars. Conceptual only — no file paths, function names, class names, or symbol names. The body is where specifics go.
- **Body:** omit when the subject is self-explanatory. Bullets are short noun phrases naming what changed; they do not justify the design. If a one-line diff needs three lines to explain, rewrite the subject.
- **Trivial changes** (typo, gitignore tweak, single-line dep bump, file rename, file move): subject alone, no body.
- **No internal references:** don't mention the review file, scratch notes, or session-specific decisions in the commit. The message should read correctly six months later with no context.
- **One logical change per commit.** Never bundle unrelated changes.

### How to write the commit

Before writing the message, run `git diff HEAD` (not just `git status --short`) so the bullets come from the actual diff, not from memory. `git status` only lists file names; it is not enough.

When uncommitted changes belong to more than one logical commit (e.g. a file has both a bug fix and a refactor mixed in), use `git add -p` to stage hunks selectively. Verify with `git diff --cached --stat` before committing.

Group ALL uncommitted changes into logical commits — never assume previous changes were already committed. If the tree has 24 modified files, propose 2-3 commits, not one mega-commit.

### Proposing commits to the user

When the user asks for commits, output both the `git add` and the `git commit` commands ready to copy-paste. Subject is conceptual; body names what changed.

A typical feature commit:

```sh
git add llm_framework/core/agent.py tests/unit/test_agent.py
git commit -m "feat(agent): report billed token total in run output

- New total_billable_tokens field equals prompt + completion
- reasoning_tokens documented as a subset of completion"
```

A refactor, same convention:

```sh
git add llm_framework/core/agent.py \
        llm_framework/core/orchestrator.py
git commit -m "refactor(agent): route events through the global observability hook

- Drop on_event parameter from Agent and Orchestrator
- Add delegated_to on Agent.run for caller correlation
- Stop Orchestrator.delegate() from mutating sub-agent state
- Add observability.print_hook() helper for examples and debugging
- Migrate all 17 call sites: tests, integration, examples"
```

A trivial change (subject alone, no body):

```sh
git add .gitignore
git commit -m "chore(repo): add trailing slash to diagnostics in gitignore"
```

```sh
git rm --cached uv.lock
git commit -m "chore(repo): untrack uv.lock"
```

If the split needs `git add -p`, explain why and walk through it. If a commit would leave the tree in a broken state (e.g. the source change is in commit A but the test update is in commit B), say so and bundle them.

## Open Work (High Priority)

These are the top items from the private review notes (`issues/REVIEW_*.md`, gitignored) that should be tackled before v1.0. Items #1, #3, #6, #7, and #22 are now closed — see the review file for the commit history. The remaining top priorities:

1. **Decide on OIDC IdP coupling** — either commit to a specific IdP and rename, or remove the `v1` and `appid` fallbacks. (ISSUES #2)
2. **Move `tools/` and `mcp_servers/` to `examples/`** — capture the security patterns in `docs/patterns/security-tools.md` first. (ISSUES #8, #13)
3. **Add CI for tests + lint + types** — currently only docs deploy runs on push. Once the workflow lands, update the CI badge URL in `README.md` to point at it. (ISSUES #19)
4. **`MemoryStore` concurrency** — JSON-as-a-DB has no multi-process safety. Document the limit or swap to SQLite. (ISSUES #4)
5. **`RAGStore` hardcoded home-dir sandbox** — make the root a constructor argument. (ISSUES #5)

For the full list, see the private review notes (in `issues/REVIEW_*.md`, gitignored).
