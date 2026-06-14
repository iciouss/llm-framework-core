# Canonical exemplar for unit-test-agent. Read before creating a new one.
import json

from llm_framework.core import Agent
from llm_framework.core.tools import tool


@tool
def echo(text: str) -> str:
    """Return the input unchanged.

    Args:
        text: Text to echo.
    """
    return text


def _tool_call(name: str, args: dict, call_id: str = "tc1") -> dict:
    return {
        "choices": [{"message": {"role": "assistant", "content": None, "tool_calls": [
            {"id": call_id, "function": {"name": name, "arguments": json.dumps(args)}}
        ]}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5},
    }


def _answer(text: str) -> dict:
    return {
        "choices": [{"message": {"role": "assistant", "content": text, "tool_calls": None}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5},
    }


async def test_direct_answer(mock_llm):
    client = mock_llm(["hello"])
    result = await Agent(client).run("hi")
    assert result["answer"] == "hello"


async def test_tool_call_then_answer(mock_llm):
    client = mock_llm([_tool_call("echo", {"text": "x"}), _answer("done")])
    result = await Agent(client, tools=[echo]).run("go")
    assert result["answer"] == "done"


async def test_emits_observability_events(mock_llm, recording_hook):
    client = mock_llm([_tool_call("echo", {"text": "x"}), _answer("done")])
    await Agent(client, tools=[echo]).run("go")
    types = [e.event_type for e in recording_hook.events]
    assert "action" in types
    assert "observation" in types
