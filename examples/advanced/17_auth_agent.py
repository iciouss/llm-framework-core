"""
17 — Authentication & Authorization

Role-based access control (RBAC) with per-user ACL overrides.
Three users run the same prompt — each sees only the tools their role allows.

New here: AuthGate, MemoryPolicyBackend, StaticAuthProvider, AuthContext,
          auth_gate on Agent, auth_context on agent.run().
"""

import asyncio

from llm_framework.core import LLMClient, Agent
from llm_framework.extensions.auth import (
    AuthContext,
    AuthGate,
    MemoryPolicyBackend,
    StaticAuthProvider,
)
from llm_framework.tools import get_current_datetime, fetch_url, add_numbers, write_file

POLICY = {
    "roles": {
        "admin": {"tools": ["*"]},
        "analyst": {"tools": ["fetch_url", "get_current_datetime"]},
        "viewer": {"tools": ["get_current_datetime"]},
    },
    "users": {
        # alice inherits analyst + one extra ACL grant
        "alice": {"roles": ["analyst"], "extra_tools": ["add_numbers"]},
        "bob": {"roles": ["viewer"]},
        "svc": {"roles": ["admin"]},
    },
}

ALL_TOOLS = [get_current_datetime, fetch_url, add_numbers, write_file]

provider = StaticAuthProvider(
    users={
        "alice": AuthContext(user_id="alice", roles={"analyst"}),
        "bob": AuthContext(user_id="bob", roles={"viewer"}),
        "svc": AuthContext(user_id="svc", roles={"admin"}),
    }
)


def on_event(e: dict):
    if e["event"] == "action":
        print(f"    -> {e['tool']}()")
    elif e["event"] == "tool_error":
        print(f"    !! {e['error']}")
    elif e["event"] == "answer":
        print(f"    {e['content']}")


async def main():
    gate = AuthGate(MemoryPolicyBackend(POLICY))

    async with LLMClient.from_env() as client:
        agent = Agent(
            client, tools=ALL_TOOLS, auth_gate=gate, temperature=0.0, on_event=on_event
        )

        for username in ["bob", "alice", "svc"]:
            ctx = await provider.resolve({"type": "username", "username": username})
            visible = [
                s["function"]["name"] for s in gate.filter_schemas(agent.schemas, ctx)
            ]
            print(f"\n[{username}] roles={ctx.roles} | tools={visible}")
            await agent.run("What time is it? Then add 10 and 32.", auth_context=ctx)


if __name__ == "__main__":
    asyncio.run(main())
