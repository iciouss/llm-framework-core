"""
test_auth.py — Integration tests for the auth extension.

These tests do NOT require a running LLM. They exercise the AuthGate,
PolicyBackend, and Agent integration directly using a mock LLM client that
records the tool schemas it receives.

Run:
    python tests/core/test_auth.py
"""

import asyncio
import json
import pathlib
import tempfile

from llm_framework.extensions.auth import (
    AuthContext,
    AuthGate,
    FilePolicyBackend,
    MemoryPolicyBackend,
    StaticAuthProvider,
)
from llm_framework.core import Agent
from llm_framework.core.tools import tool

# ---------------------------------------------------------------------------
# Dummy tools for testing — no real I/O
# ---------------------------------------------------------------------------


@tool
def tool_a() -> str:
    "Tool A."
    return "a"


@tool
def tool_b() -> str:
    "Tool B."
    return "b"


@tool
def tool_c() -> str:
    "Tool C."
    return "c"


ALL_TOOLS = [tool_a, tool_b, tool_c]

# ---------------------------------------------------------------------------
# Mock LLM client — captures what schemas the agent sends to the model
# ---------------------------------------------------------------------------


class MockLLMClient:
    """Records every chat_completions call so tests can inspect visible schemas."""

    def __init__(self, final_answer: str = "done"):
        self.calls: list[dict] = []
        self._final_answer = final_answer

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        pass

    async def chat_completions(self, messages, tools=None, **kwargs) -> dict:
        self.calls.append({"messages": messages, "tools": tools or []})
        # always return a final answer with no tool calls so the loop terminates
        return {
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": self._final_answer,
                        "tool_calls": None,
                    }
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }


# ---------------------------------------------------------------------------
# Policy fixture
# ---------------------------------------------------------------------------

POLICY = {
    "roles": {
        "admin": {"tools": ["*"]},
        "analyst": {"tools": ["tool_a", "tool_b"]},
        "viewer": {"tools": ["tool_a"]},
    },
    "users": {
        "alice": {"roles": ["analyst"]},
        "bob": {"roles": ["viewer"], "extra_tools": ["tool_c"]},
        "svc": {"roles": ["admin"]},
        # dave has no role and no grants — should see nothing
        "dave": {"roles": []},
    },
}

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def make_gate(policy: dict) -> AuthGate:
    return AuthGate(MemoryPolicyBackend(policy))


def visible_names(gate: AuthGate, schemas: list, ctx: AuthContext) -> list[str]:
    return [s["function"]["name"] for s in gate.filter_schemas(schemas, ctx)]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_schema_filtering_analyst():
    gate = make_gate(POLICY)
    ctx = AuthContext(user_id="alice", roles={"analyst"})
    schemas = [t.schema for t in ALL_TOOLS]
    names = visible_names(gate, schemas, ctx)
    assert names == ["tool_a", "tool_b"], f"analyst sees wrong tools: {names}"
    print("PASS  test_schema_filtering_analyst")


def test_schema_filtering_viewer_with_extra_acl():
    gate = make_gate(POLICY)
    ctx = AuthContext(user_id="bob", roles={"viewer"})
    schemas = [t.schema for t in ALL_TOOLS]
    names = visible_names(gate, schemas, ctx)
    # viewer role gives tool_a; extra_tools ACL adds tool_c
    assert set(names) == {"tool_a", "tool_c"}, f"viewer+acl sees wrong tools: {names}"
    print("PASS  test_schema_filtering_viewer_with_extra_acl")


def test_schema_filtering_admin_wildcard():
    gate = make_gate(POLICY)
    ctx = AuthContext(user_id="svc", roles={"admin"})
    schemas = [t.schema for t in ALL_TOOLS]
    names = visible_names(gate, schemas, ctx)
    assert set(names) == {
        "tool_a",
        "tool_b",
        "tool_c",
    }, f"admin sees wrong tools: {names}"
    print("PASS  test_schema_filtering_admin_wildcard")


def test_schema_filtering_no_grants():
    gate = make_gate(POLICY)
    ctx = AuthContext(user_id="dave", roles=set())
    schemas = [t.schema for t in ALL_TOOLS]
    names = visible_names(gate, schemas, ctx)
    assert names == [], f"user with no grants should see no tools, got: {names}"
    print("PASS  test_schema_filtering_no_grants")


def test_pass_through_when_no_context():
    gate = make_gate(POLICY)
    schemas = [t.schema for t in ALL_TOOLS]
    # None context = no auth configured — all tools pass through
    names = visible_names(gate, schemas, None)
    assert set(names) == {"tool_a", "tool_b", "tool_c"}, f"pass-through broken: {names}"
    print("PASS  test_pass_through_when_no_context")


def test_authorize_allows_permitted_tool():
    gate = make_gate(POLICY)
    ctx = AuthContext(user_id="alice", roles={"analyst"})
    assert gate.authorize("tool_a", ctx) is True
    assert gate.authorize("tool_b", ctx) is True
    print("PASS  test_authorize_allows_permitted_tool")


def test_authorize_denies_forbidden_tool():
    gate = make_gate(POLICY)
    ctx = AuthContext(user_id="alice", roles={"analyst"})
    assert gate.authorize("tool_c", ctx) is False
    print("PASS  test_authorize_denies_forbidden_tool")


def test_authorize_admin_wildcard():
    gate = make_gate(POLICY)
    ctx = AuthContext(user_id="svc", roles={"admin"})
    assert gate.authorize("tool_a", ctx) is True
    assert gate.authorize("tool_c", ctx) is True
    assert gate.authorize("anything_unknown", ctx) is True
    print("PASS  test_authorize_admin_wildcard")


def test_denied_tools_acl():
    policy = {
        "roles": {"editor": {"tools": ["tool_a", "tool_b", "tool_c"]}},
        "users": {"carol": {"roles": ["editor"], "denied_tools": ["tool_c"]}},
    }
    gate = make_gate(policy)
    ctx = AuthContext(user_id="carol", roles={"editor"})
    schemas = [t.schema for t in ALL_TOOLS]
    names = visible_names(gate, schemas, ctx)
    assert "tool_c" not in names, f"denied_tools not respected: {names}"
    assert set(names) == {"tool_a", "tool_b"}
    print("PASS  test_denied_tools_acl")


async def test_agent_schema_filtering_integration():
    """Agent sends only allowed schemas to the LLM."""
    gate = make_gate(POLICY)
    client = MockLLMClient()
    ctx = AuthContext(user_id="alice", roles={"analyst"})

    agent = Agent(client, tools=ALL_TOOLS, auth_gate=gate)
    await agent.run("do something", auth_context=ctx)

    sent_names = [t["function"]["name"] for t in client.calls[0]["tools"]]
    assert set(sent_names) == {
        "tool_a",
        "tool_b",
    }, f"agent sent wrong schemas: {sent_names}"
    print("PASS  test_agent_schema_filtering_integration")


async def test_agent_execution_time_denial():
    """Execution-time check blocks unauthorized tool calls even if the model tries."""
    gate = make_gate(POLICY)

    # mock client that forces a tool_c call on the first step, then answers
    class ForcedToolCallClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_):
            pass

        _step = 0

        async def chat_completions(self, messages, tools=None, **kwargs):
            self._step += 1
            if self._step == 1:
                return {
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": None,
                                "tool_calls": [
                                    {
                                        "id": "tc1",
                                        "function": {
                                            "name": "tool_c",
                                            "arguments": "{}",
                                        },
                                    }
                                ],
                            }
                        }
                    ],
                    "usage": {"prompt_tokens": 10, "completion_tokens": 5},
                }
            return {
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "done",
                            "tool_calls": None,
                        }
                    }
                ],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5},
            }

    errors = []

    def on_event(e):
        if e["event"] == "tool_error":
            errors.append(e)

    ctx = AuthContext(user_id="alice", roles={"analyst"})
    agent = Agent(
        ForcedToolCallClient(), tools=ALL_TOOLS, auth_gate=gate, on_event=on_event
    )
    result = await agent.run("do something", auth_context=ctx)

    assert any(
        "access_denied" in str(e.get("reason", "")) for e in errors
    ), f"expected access_denied tool_error, got: {errors}"
    print("PASS  test_agent_execution_time_denial")


async def test_backward_compat_no_auth_gate():
    """Agent without auth_gate behaves identically to before — all tools visible."""
    client = MockLLMClient()
    agent = Agent(client, tools=ALL_TOOLS)
    # no auth_context, no auth_gate — all three tools should reach the LLM
    await agent.run("do something")
    sent_names = {t["function"]["name"] for t in client.calls[0]["tools"]}
    assert sent_names == {
        "tool_a",
        "tool_b",
        "tool_c",
    }, f"backward compat broken: {sent_names}"
    print("PASS  test_backward_compat_no_auth_gate")


async def test_file_policy_backend():
    """FilePolicyBackend loads JSON from disk and resolves permissions correctly."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".json", delete=False, encoding="utf-8"
    ) as f:
        json.dump(POLICY, f)
        path = pathlib.Path(f.name)

    try:
        backend = FilePolicyBackend(path)
        gate = AuthGate(backend)
        ctx = AuthContext(user_id="svc", roles={"admin"})
        schemas = [t.schema for t in ALL_TOOLS]
        names = visible_names(gate, schemas, ctx)
        assert set(names) == {"tool_a", "tool_b", "tool_c"}
        print("PASS  test_file_policy_backend")
    finally:
        path.unlink(missing_ok=True)


async def test_static_auth_provider():
    provider = StaticAuthProvider(
        api_keys={"sk-abc": AuthContext(user_id="svc", roles={"admin"})},
        users={"alice": AuthContext(user_id="alice", roles={"analyst"})},
    )
    ctx_api = await provider.resolve({"type": "api_key", "key": "sk-abc"})
    ctx_user = await provider.resolve({"type": "username", "username": "alice"})
    ctx_miss = await provider.resolve({"type": "api_key", "key": "wrong"})
    assert ctx_api is not None and ctx_api.user_id == "svc"
    assert ctx_user is not None and ctx_user.user_id == "alice"
    assert ctx_miss is None
    print("PASS  test_static_auth_provider")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------


async def run_all():
    # sync tests
    test_schema_filtering_analyst()
    test_schema_filtering_viewer_with_extra_acl()
    test_schema_filtering_admin_wildcard()
    test_schema_filtering_no_grants()
    test_pass_through_when_no_context()
    test_authorize_allows_permitted_tool()
    test_authorize_denies_forbidden_tool()
    test_authorize_admin_wildcard()
    test_denied_tools_acl()

    # async tests
    await test_agent_schema_filtering_integration()
    await test_agent_execution_time_denial()
    await test_backward_compat_no_auth_gate()
    await test_file_policy_backend()
    await test_static_auth_provider()

    print("\nAll auth tests passed.")


if __name__ == "__main__":
    asyncio.run(run_all())
