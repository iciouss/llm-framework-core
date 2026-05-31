import json

import pytest

from llm_framework.core import Agent, LLMClient, Orchestrator
from llm_framework.extensions import MCPClient, MCPManager

pytestmark = pytest.mark.integration

# Requires: uv pip install -e ".[mcp,rag,qdrant]"
# knowledge-server also needs a live embeddings endpoint (EMBED_MODEL or LLM_MODEL in .env)


def on_event(e):
    print(
        f"[{e['event'].upper()}] {json.dumps({k: v for k, v in e.items() if k != 'event'})}"
    )


async def main():
    knowledge_bridge = MCPClient.stdio("uv", ["run", "knowledge-server"])
    memory_bridge = MCPClient.stdio("uv", ["run", "memory-server"])

    async with (
        MCPManager([knowledge_bridge]) as knowledge_mcp,
        MCPManager([memory_bridge]) as memory_mcp,
        LLMClient.from_env() as client,
    ):
        knowledge_tools = await knowledge_mcp.get_all_tools()
        memory_tools = await memory_mcp.get_all_tools()

        # knowledge agent: ingests files and searches them
        knowledge_agent = Agent(
            client=client,
            tools=knowledge_tools,
            max_steps=5,
            on_event=on_event,
            max_tokens=4096,
        )

        # memory agent: persists and recalls facts
        memory_agent = Agent(
            client=client,
            tools=memory_tools,
            max_steps=5,
            on_event=on_event,
            max_tokens=4096,
        )

        orchestrator = Orchestrator(
            client=client,
            sub_agents={
                "knowledge": knowledge_agent,
                "memory": memory_agent,
            },
            max_tokens=4096,
        )

        from pathlib import Path

        readme = str(Path(__file__).parent.parent.parent / "README.md")

        result = await orchestrator.run(
            f"I want to understand the project at {readme} and be able to answer questions about it later. "
            "I need you to extract the key information from the README and store it in memory. Then, when I ask you questions about the project, "
            "you should recall relevant information from memory and use it to answer my questions. "
            "Figure out what you need to do with the agents available to you."
        )

        print("\n--- ANSWER ---")
        print(result["answer"])


async def test_main():
    await main()
