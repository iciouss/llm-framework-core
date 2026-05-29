# llm-framework

Minimal Python library for building LLM-powered agents with a low dependency footprint.

- **`core/`** needs only `httpx` and `python-dotenv`. Always available.
- **`extensions/`** are optional extras. Pull only what you need.
- Every feature targets the "goldilocks" zone: use a library where it saves meaningful complexity, write from scratch where it adds unnecessary dependencies.

______________________________________________________________________

## Where to go next

- **[Installation](https://iciouss.github.io/llm-framework/getting-started/installation/index.md)**: Learn how to install the core library and its optional extensions.
- **[Quickstart](https://iciouss.github.io/llm-framework/getting-started/quickstart/index.md)**: Build your first agent in less than 15 lines of code.
- **[Patterns](https://iciouss.github.io/llm-framework/patterns/index.md)**: Architecture guidance for choosing `tools/` or `mcp_servers/`.

______________________________________________________________________

## API Reference Overview

- **[Core](https://iciouss.github.io/llm-framework/api/core/index.md)** — `LLMClient`, `Agent`, `Orchestrator`, `HistoryBuffer`, `@tool`, `@cached_tool`
- **[Extensions](https://iciouss.github.io/llm-framework/api/extensions/index.md)** — `MCPClient`, `MCPManager`, `MCPServer`, `MCPContext`, `MemoryStore`, `RAGStore`, auth gate, `OIDCAuthProvider`, guardrails, vector stores
- **[Tools](https://iciouss.github.io/llm-framework/api/tools/index.md)** — Filesystem, shell, web fetch, calculator, clock, memory
- **[Configuration](https://iciouss.github.io/llm-framework/api/config/index.md)** — `Config` dataclass
