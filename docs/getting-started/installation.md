# Installation

This page covers practical installation paths for different workflows.

Use source install if you are developing in this repository.
Use wheel install if you want to consume a pinned release artifact without cloning the repo.

## Choose an installation path

- **Source install (recommended for contributors)**: best for local development, examples, and tests.
- **Release wheel install**: best for consumers pinning to a specific GitHub release.

## Source install (recommended for this repo)

```bash
uv venv && source .venv/bin/activate
uv pip install -e .
```

Install optional capabilities only when needed:

```bash
uv pip install -e ".[rag]"      # pypdf + semantic-text-splitter
uv pip install -e ".[qdrant]"   # Qdrant vector backend
uv pip install -e ".[oidc]"     # OIDC provider support
uv pip install -e ".[all]"      # all library extras: rag, qdrant, oidc
uv sync --group examples        # library extras + web (fastapi/uvicorn/websockets); run before any example
```

This keeps dependencies explicit and aligned with the framework's low-footprint philosophy.

## Release wheel install

Because `llm-framework` is distributed via GitHub Releases (instead of PyPI), you can install a `.whl` directly.

## Base Installation

To install the minimal core (which only requires `httpx` and `python-dotenv`), run:

```bash
pip install "https://<PAT>@github.com/<owner>/llm-framework/releases/download/v0.1.0/llm_framework-0.1.0-py3-none-any.whl"
```

!!! warning "GitHub PAT Required"
    You must replace `<PAT>` in the URL with a GitHub fine-grained Personal Access Token. This token must have `contents: read` permissions for the repository.

## Optional Extras

If you need specific extensions, you can install them using bracket notation at the end of the wheel URL. Pull only what you need to keep your dependency footprint small.

```bash
# Install with Retrieval-Augmented Generation (RAG) support
pip install "https://<PAT>@github.com/<owner>/llm-framework/releases/download/v0.1.0/llm_framework-0.1.0-py3-none-any.whl[rag]"

# Install all library extras (rag, qdrant, oidc)
pip install "https://<PAT>@github.com/<owner>/llm-framework/releases/download/v0.1.0/llm_framework-0.1.0-py3-none-any.whl[all]"
```

After installation, continue with the Quickstart to verify your environment and run a first agent.