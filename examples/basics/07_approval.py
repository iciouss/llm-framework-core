"""
07 — Human-in-the-Loop (Approval Callbacks)

Gate tool execution behind a human approval step.
The agent emits a "waiting_for_approval" event and pauses
before calling any tool in the approval_tools list.

New here: approval_callback, approval_tools.
  approval_tools=None  — gates every tool
  approval_tools=[...] — scopes it to specific tool names only
"""

import asyncio
import json

from llm_framework.core import LLMClient, Agent, tool


@tool
def read_report(name: str) -> str:
    "Read a named report. Safe, read-only."
    return f"[contents of report '{name}': quarterly revenue up 12%]"


@tool
def send_email(to: str, subject: str, body: str) -> str:
    "Send an email to a recipient."
    return f"Email sent to {to} with subject '{subject}'."


@tool
def delete_record(record_id: str) -> str:
    "Permanently delete a record by ID."
    return f"Record {record_id} deleted."


async def approval_callback(name: str, args: dict) -> bool:
    print(f"\n  [APPROVAL REQUIRED] Tool: {name}")
    print(f"  Arguments: {json.dumps(args, indent=2)}")
    answer = input("  Approve? [y/n] ").strip().lower()
    return answer == "y"


# Only surface the action and its outcome — the approval prompt itself
# is printed by the callback, so no need to duplicate it here.
def show_approval_flow(e: dict):
    if e["event"] == "action":
        print(f"  [will call] {e.get('tool')}")
    elif e["event"] == "observation":
        print(f"  [result]    {str(e.get('content', ''))[:100]}")
    elif e["event"] == "tool_error":
        print(f"  [denied]    {e.get('error', '')}")


async def main():
    async with LLMClient.from_env() as client:
        agent = Agent(
            client=client,
            tools=[read_report, send_email, delete_record],
            # only these two require human approval before executing
            approval_callback=approval_callback,
            approval_tools=["send_email", "delete_record"],
            on_event=show_approval_flow,
        )

        result = await agent.run(
            "Read the Q4 report, then email a summary to cfo@company.com."
        )

        print("\n--- ANSWER ---")
        print(result["answer"])
        print(
            f"[tokens] prompt={result['prompt_tokens']} completion={result['completion_tokens']}"
        )


if __name__ == "__main__":
    asyncio.run(main())
