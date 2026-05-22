import asyncio
import json
from pathlib import Path

from llm_framework.core import LLMClient, Agent
from llm_framework.extensions import MCPClient, MCPManager

# The knowledge server is spawned as a subprocess — no manual server startup needed.
# Requires: uv pip install -e ".[rag,qdrant,mcp]"
# Requires: live embeddings endpoint at LLM_BASE_URL (set EMBED_MODEL if different from LLM_MODEL)

# Ingest the repo README as test data — always present, has real content
TEST_FILE = str(Path(__file__).parent.parent.parent / "README.md")


async def main():
    servers = [
        MCPClient.stdio("uv", ["run", "knowledge-server"]),
    ]

    async with (
        MCPManager(servers) as mcp,
        LLMClient.from_env() as client,
    ):
        mcp_tools = await mcp.get_all_tools()

        agent = Agent(
            client=client,
            tools=mcp_tools,
            max_steps=5,
            on_event=lambda e: print(
                f"[{e['event'].upper()}] {json.dumps({k: v for k, v in e.items() if k != 'event'})}"
            ),
        )

        # ingest before querying — in-memory backend starts empty each run
        ingest_result = await agent.run(f"Ingest the file at path: {TEST_FILE}")
        print("\n--- INGEST ---")
        print(ingest_result["answer"])

        # now query what was ingested
        search_result = await agent.run(
            "Search the knowledge base and summarize what you find about the project architecture."
        )
        print("\n--- SEARCH ---")
        print(search_result["answer"])


if __name__ == "__main__":
    asyncio.run(main())
