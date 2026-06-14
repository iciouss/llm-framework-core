# Canonical exemplar for mcp-server. Read before creating a new one.
import argparse
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import uvicorn

from llm_framework.extensions.mcp import MCPContext, MCPServer


@asynccontextmanager
async def lifespan(server: MCPServer) -> AsyncIterator[dict]:
    async with SomeResource.from_env() as resource:
        yield {"resource": resource}


mcp = MCPServer("my-server", lifespan=lifespan)


@mcp.tool()
async def create_item(name: str, value: str, ctx: MCPContext) -> str:
    """Create an item in the store.

    Args:
        name: Item name.
        value: Item value.
    """
    resource = ctx.lifespan["resource"]
    ...


@mcp.tool()
async def find_item(query: str, ctx: MCPContext, limit: int = 5) -> str:
    """Search for items matching a query.

    Args:
        query: Search query.
        limit: Max results (default 5).
    """
    resource = ctx.lifespan["resource"]
    ...


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--http", action="store_true")
    parser.add_argument("--port", type=int, default=8083)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    if args.http:
        uvicorn.run(mcp.http_app(), host=args.host, port=args.port, log_level="warning")
    else:
        mcp.run()


if __name__ == "__main__":
    main()
