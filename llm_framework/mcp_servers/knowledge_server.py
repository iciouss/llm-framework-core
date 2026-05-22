import argparse
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from llm_framework.extensions.rag import RAGStore, backend_from_env
from llm_framework.extensions.mcp import MCPContext, MCPServer

_MAX_CHARS = 8_000


@asynccontextmanager
async def lifespan(server: MCPServer) -> AsyncIterator[dict]:
    async with RAGStore.from_env(backend_from_env()) as rag:
        yield {"rag": rag}


mcp = MCPServer("knowledge", lifespan=lifespan)


# --- tools ---


@mcp.tool()
async def search_notes(query: str, ctx: MCPContext, limit: int = 3) -> str:
    """Search the knowledge base for relevant chunks.

    Args:
        query: Search query to find relevant knowledge chunks.
        limit: Maximum number of results to return (default 3).
    """
    rag: RAGStore = ctx.lifespan["rag"]
    results = await rag.search(query, limit=limit)
    if not results:
        return "No results found."
    text = "\n\n---\n\n".join(results)
    return text[:_MAX_CHARS] + ("\n...[truncated]" if len(text) > _MAX_CHARS else "")


@mcp.tool()
async def ingest_file(path: str, ctx: MCPContext) -> str:
    """Ingest a file into the knowledge base.

    Args:
        path: Absolute or relative path to the file to ingest.
    """
    resolved = Path(path).expanduser().resolve()
    try:
        resolved.relative_to(Path.home())
    except ValueError:
        raise PermissionError(
            f"Path '{resolved}' is outside the home directory sandbox"
        )
    rag: RAGStore = ctx.lifespan["rag"]
    count = await rag.ingest_file(str(resolved))
    return f"Ingested {count} chunks from '{resolved}'."


# --- entry point ---


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--http", action="store_true")
    parser.add_argument("--port", type=int, default=8082)
    args = parser.parse_args()

    if args.http:
        import uvicorn

        uvicorn.run(mcp.http_app(), host="0.0.0.0", port=args.port, log_level="warning")
    else:
        mcp.run()


if __name__ == "__main__":
    main()
