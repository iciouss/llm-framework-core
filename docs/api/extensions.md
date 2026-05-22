# Extensions

Extensions are optional modules that add capabilities beyond the core runtime while keeping dependencies explicit.
Use extensions when you need integration features like MCP connectivity, RAG storage, policy-based auth, or output safeguards.

## MCP

MCP extensions connect your agents to out-of-process tool servers over stdio or streamable HTTP.
Use `MCPClient`/`MCPManager` to consume tools from any MCP server. Use `MCPServer`/`MCPContext` to build and expose your own.

### ::: llm_framework.extensions.mcp.MCPClient

### ::: llm_framework.extensions.mcp.MCPManager

### ::: llm_framework.extensions.mcp.MCPServer

### ::: llm_framework.extensions.mcp.MCPContext

---

## Memory

`MemoryStore` is a lightweight key-value persistence layer for recalled context.
It is useful for user preferences, session facts, and other simple memory patterns without adding heavy dependencies.

### ::: llm_framework.extensions.memory.MemoryStore

---

## Auth

Auth primitives separate authentication (who the caller is) from authorization (which tools they can use).
Use these types when your agent must enforce role-based or user-based access to tools.

### ::: llm_framework.extensions.auth.AuthContext

### ::: llm_framework.extensions.auth.AuthGate

### ::: llm_framework.extensions.auth.backends.file.FilePolicyBackend

### ::: llm_framework.extensions.auth.backends.memory.MemoryPolicyBackend

### ::: llm_framework.extensions.auth.providers.static.StaticAuthProvider

### ::: llm_framework.extensions.auth.providers.oidc.OIDCAuthProvider

---

## RAG

`RAGStore` handles ingest, chunking, embedding, and semantic retrieval workflows.
Use it when your agent should ground answers in your own documents rather than only model priors.

### ::: llm_framework.extensions.rag.RAGStore

---

## Vector Store

Vector backends provide the storage/search engine behind RAG retrieval.
`QdrantBackend` is the default implementation and supports local, in-memory, and remote modes.

### ::: llm_framework.extensions.rag.vector_store.qdrant.QdrantBackend

---

## Guardrails

Guardrails are composable filters that validate or transform agent input and output.
Use them to block unsafe prompts, redact sensitive output, or enforce policy boundaries.

### ::: llm_framework.extensions.guardrails.block_keywords

### ::: llm_framework.extensions.guardrails.strip_pii

### ::: llm_framework.extensions.guardrails.llm_guard
