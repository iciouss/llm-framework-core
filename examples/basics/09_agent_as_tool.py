"""
09 — Agent as a Tool (Remote Agent Delegation)

A running agent server exposes one tool — delegate_to_{name}(task) — over MCP.
Your local agent calls it like any other tool, with no knowledge of
the remote agent's tools, LLM, or system prompt.

New here: MCPClient spawning an agent server, timeout for long-running ReAct loops.
"""

import asyncio
from pathlib import Path

from llm_framework.core import Agent, LLMClient
from llm_framework.extensions import MCPClient, MCPManager

# Resolve the agent server path relative to this file.
RESEARCHER = str(
    Path(__file__).parent.parent.parent
    / "examples"
    / "specialized_agents"
    / "researcher_agent.py"
)


# The interesting moment here is the delegation: task sent out, answer received.
def log_delegation(e: dict):
    if e["event"] == "action":
        task = e.get("args", {}).get("task", "")
        print(f"  [delegating to {e.get('tool')}] {str(task)[:120]}")
    elif e["event"] == "observation":
        print(f"  [remote answer] {str(e.get('content', ''))[:200]}")
    elif e["event"] == "tool_error":
        print(f"  [delegation failed] {e.get('error', '')}")


async def main():
    # Spawn the researcher agent as a subprocess — it runs its own ReAct loop internally.
    # Alternative (pre-running HTTP server): MCPClient.http("http://localhost:8090/mcp", timeout=300.0)
    # The timeout=300.0 on HTTP gives the remote agent up to 5 minutes to complete.
    async with (
        MCPManager([MCPClient.stdio("uv", ["run", "python", RESEARCHER])]) as mcp,
        LLMClient.from_env() as client,
    ):
        # The remote agent's tool appears here like any local tool.
        remote_tools = await mcp.get_all_tools()
        print(f"Remote tools available: {[t.name for t in remote_tools]}\n")

        agent = Agent(
            client=client,
            tools=remote_tools,
            max_tokens=2048,
            on_event=log_delegation,
        )

        result = await agent.run(
            "Research what Python asyncio is and give me a two-sentence explanation I can share with a junior developer."
        )

        print("\n--- ANSWER ---")
        print(result["answer"])
        print(
            f"[tokens] prompt={result['prompt_tokens']} completion={result['completion_tokens']}"
        )


if __name__ == "__main__":
    asyncio.run(main())
