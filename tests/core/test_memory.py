import asyncio
import json

from llm_framework.core import LLMClient, Agent
from llm_framework.extensions import MCPClient, MCPManager


async def main():
    servers = [
        MCPClient.stdio("uv", ["run", "memory-server"]),
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

        result = await agent.run(
            "Save the fact that my favorite color is blue, then recall it and tell me what it is."
        )
        print("\n--- ANSWER ---")
        print(result["answer"])


asyncio.run(main())
