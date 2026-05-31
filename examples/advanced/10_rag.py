"""
10 — RAG: Retrieval-Augmented Generation

Ingest documents into a vector store, then let the agent answer
questions by searching that knowledge base semantically. The knowledge
server handles chunking, embedding, and search — the agent decides
when to ingest and when to search.

New here: knowledge-server as subprocess, ingest + search tool pattern.

Requires: uv pip install -e ".[mcp,rag,qdrant]"
Also requires: EMBED_MODEL (or LLM_MODEL) pointing to an embeddings-capable endpoint.
"""

import asyncio
import json
from pathlib import Path

from llm_framework.core import Agent, LLMClient
from llm_framework.extensions import MCPClient, MCPManager

KNOWLEDGE_SERVER = str(
    Path(__file__).parent.parent.parent
    / "llm_framework"
    / "mcp_servers"
    / "knowledge_server.py"
)

# We'll ingest this repo's README as demo content — always present, real substance.
README = str(Path(__file__).parent.parent.parent / "README.md")


# Distinguish ingest from search visually — the two RAG operations look very different.
def trace_rag(e: dict):
    if e["event"] == "action":
        tool = e.get("tool", "")
        args = e.get("args", {})
        if "ingest" in tool:
            print(f"  [ingest] {str(args.get('file_path', args))[:100]}")
        elif "search" in tool:
            print(f"  [search] {str(args.get('query', args))[:100]}")
        else:
            print(f"  [call]   {tool} | {json.dumps(args, ensure_ascii=False)[:100]}")
    elif e["event"] == "observation":
        print(f"  [result] {str(e.get('content', ''))[:160]}")
    elif e["event"] == "tool_error":
        print(f"  [error]  {e.get('error', '')}")


async def main():
    # Spawn the knowledge server as a subprocess.
    # Alternative (pre-running HTTP server): MCPClient.http("http://localhost:8082/mcp")
    async with (
        MCPManager([MCPClient.stdio("uv", ["run", "python", KNOWLEDGE_SERVER])]) as mcp,
        LLMClient.from_env() as client,
    ):
        tools = await mcp.get_all_tools()
        print(f"RAG tools: {[t.__name__ for t in tools]}\n")

        agent = Agent(
            client=client,
            tools=tools,
            max_tokens=2048,
            system_prompt=(
                "You answer questions from a knowledge base. "
                "Always search before answering. If the knowledge base is empty, ingest the relevant file first."
            ),
            on_event=trace_rag,
        )

        print("=== Step 1: ingest ===")
        await agent.run(f"Ingest the file at: {README}")

        print("\n=== Step 2: query ===")
        result = await agent.run(
            "What optional extras does the llm-framework provide and what does each one add?"
        )

        print("\n--- ANSWER ---")
        print(result["answer"])
        print(
            f"[tokens] prompt={result['prompt_tokens']} completion={result['completion_tokens']}"
        )


if __name__ == "__main__":
    asyncio.run(main())
