from __future__ import annotations

import json
import pprint

from llm_framework.core import Agent, Orchestrator


def _delegate_tool_call(agent_name: str, task: str, call_id: str = "tc1") -> dict:
    "Build a raw LLM response that requests a delegate tool call on the supervisor."
    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": call_id,
                            "function": {
                                "name": "delegate",
                                "arguments": json.dumps(
                                    {"agent_name": agent_name, "task": task}
                                ),
                            },
                        }
                    ],
                }
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5},
    }


def _final_response(text: str) -> dict:
    "Build a raw LLM final-answer response."
    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": text,
                    "tool_calls": None,
                }
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5},
    }


async def test_orchestrator_on_event_fires_for_each_delegation(mock_llm):
    "on_event callback must receive supervisor_started, delegated, delegation_finished, supervisor_finished in order."
    sub_client = mock_llm(responses=["sub-done"])
    sub_agent = Agent(sub_client, max_steps=1)
    supervisor_responses = [
        _delegate_tool_call(agent_name="echo", task="do something"),
        _final_response("supervisor-done"),
    ]
    supervisor_client = mock_llm(responses=supervisor_responses)
    received: list[dict] = []

    def on_event(event: dict) -> None:
        received.append(event)

    orch = Orchestrator(
        client=supervisor_client,
        sub_agents={"echo": sub_agent},
        on_event=on_event,
    )
    result = await orch.run("please handle")
    pprint.pprint(received)
    assert "answer" in result
    assert [e["event"] for e in received] == [
        "supervisor_started",
        "delegated",
        "delegation_finished",
        "supervisor_finished",
    ]
    assert received[0]["sub_agent_id"] is None
    assert received[1]["sub_agent_id"] == "echo"
    assert received[1]["payload"] == {"task_preview": "do something"}
    assert received[2]["sub_agent_id"] == "echo"
    assert received[2]["payload"] == {"answer_preview": "sub-done"}
    assert received[3]["sub_agent_id"] is None
    assert received[3]["payload"] == {"answer_preview": "supervisor-done"}


async def test_orchestrator_on_event_default_none_still_works(mock_llm, recording_hook):
    "Default (no on_event) must preserve the global emit() path and leave the attribute as None."
    sub_client = mock_llm(responses=["sub-done"])
    sub_agent = Agent(sub_client, max_steps=1)
    supervisor_responses = [
        _final_response("supervisor-done"),
    ]
    supervisor_client = mock_llm(responses=supervisor_responses)
    orch = Orchestrator(
        client=supervisor_client,
        sub_agents={"echo": sub_agent},
    )
    assert orch._on_event is None
    result = await orch.run("please handle")
    assert "answer" in result
    event_types = [e.event_type for e in recording_hook.events]
    assert "supervisor_started" in event_types
    assert "supervisor_finished" in event_types


async def test_orchestrator_on_event_exception_does_not_break_run(mock_llm):
    "A misbehaving on_event callback that raises on every call must not stop the orchestrator."
    sub_client = mock_llm(responses=["sub-done"])
    sub_agent = Agent(sub_client, max_steps=1)
    supervisor_responses = [
        _delegate_tool_call(agent_name="echo", task="do something"),
        _final_response("supervisor-done"),
    ]
    supervisor_client = mock_llm(responses=supervisor_responses)

    def bad_cb(event: dict) -> None:
        raise RuntimeError("consumer blew up")

    orch = Orchestrator(
        client=supervisor_client,
        sub_agents={"echo": sub_agent},
        on_event=bad_cb,
    )
    result = await orch.run("please handle")
    assert "answer" in result
    assert result["answer"] == "supervisor-done"
