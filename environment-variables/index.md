# Environment Variables

The `llm-framework` relies on environment variables for configuration. To set up your local environment, copy the `.env.example` file to a new file named `.env` and fill in your specific values.

The table below is generated from `.env.example`, so it stays in sync with the codebase. Use it as the source of truth when configuring local runs, examples, or MCP/plugin servers.

## How to use this reference

- Start with required core variables (`LLM_BASE_URL`, `LLM_API_KEY`, `LLM_MODEL`).
- Add feature-specific variables only for the extras you installed.
- Keep provider credentials in `.env` and out of source-controlled files.

## Variable groups

- **Core model access**: base URL, API key, model name.
- **RAG/vector settings**: embedding model and backend-specific options.
- **Auth/OIDC settings**: identity provider parameters for web auth flows.
- **Plugin/server settings**: service credentials used by MCP/plugin adapters.

Below is a complete reference of all available configuration options:

| Variable             | Required | Default                                                      | Description                                                                                                                         |
| -------------------- | -------- | ------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------- |
| `LLM_BASE_URL`       | **Yes**  | `http://localhost:1234/v1`                                   | The base URL for the OpenAI-compatible LLM server.                                                                                  |
| `LLM_API_KEY`        | **Yes**  | `nokey`                                                      | The API key for the LLM server.                                                                                                     |
| `LLM_MODEL`          | **Yes**  | `google/gemma-4-e4b`                                         | The underlying model to use.                                                                                                        |
| `EMBED_MODEL`        | No       | `nomic-embed-text`                                           | Embeddings model. Falls back to LLM_MODEL if unset. Set this when your embeddings model differs from your chat model (common case). |
| `CA_BUNDLE_PATH`     | No       | `./custom-ca.crt`                                            | Path to a custom CA bundle (.crt / .pem). Leave unset to use system default.                                                        |
| `VECTOR_BACKEND`     | No       | `qdrant`                                                     | Vector store backend. Supported values: qdrant.                                                                                     |
| `QDRANT_COLLECTION`  | No       | `knowledge_base`                                             | Qdrant collection name.                                                                                                             |
| `QDRANT_VECTOR_SIZE` | No       | `768`                                                        | Must match your embedding model's output dimension.                                                                                 |
| `QDRANT_PATH`        | No       | `./data/qdrant`                                              | Local persistent storage path. Unset = in-memory.                                                                                   |
| `OIDC_CLIENT_ID`     | No       | `chat-agent`                                                 | OAuth2 client ID (required for example 18.2_web_oidc_agent.py).                                                                     |
| `OIDC_CLIENT_SECRET` | No       | `chat-agent-secret`                                          | OAuth2 client secret.                                                                                                               |
| `OIDC_DISCOVERY_URL` | No       | `http://localhost:5556/dex/.well-known/openid-configuration` | Full URL to the provider's OpenID Connect discovery document.                                                                       |
| `OIDC_REDIRECT_URI`  | No       | `http://127.0.0.1:8080/auth/callback`                        | Callback URL registered with the provider. Defaults to http://127.0.0.1:8080/auth/callback.                                         |
| `OIDC_ROLES_CLAIM`   | No       | `roles`                                                      | JWT claim that carries role strings. Defaults to "roles".                                                                           |
| `QDRANT_URL`         | No       | `http://localhost:6333`                                      | Remote cluster URL. Takes precedence over QDRANT_PATH.                                                                              |
| `MEMORY_PATH`        | No       | `./data/memory.json`                                         | Memory MCP server path. Defaults to in-memory (lost on server restart).                                                             |
