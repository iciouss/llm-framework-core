"""
08 — Multi-Agent Orchestration

The Orchestrator creates a supervisor agent with a delegate() tool
injected automatically. The supervisor decides which sub-agent to
call and what task to hand off — you just define the sub-agents
and give the supervisor a high-level goal.

New here: Orchestrator, sub_agents dict, make_step_printer factory for labeled output.
"""

import asyncio
import json
from pathlib import Path

from llm_framework.core import LLMClient, Agent, Orchestrator, tool


# --- Sub-agent A: knows about the filesystem ---
@tool
def list_directory(path: str) -> str:
    "List the files and folders at the given path. Returns one entry per line."
    p = Path(path).expanduser()
    if not p.exists():
        return f"Path does not exist: {path}"
    entries = sorted(p.iterdir(), key=lambda e: (e.is_file(), e.name))
    return "\n".join(e.name + ("/" if e.is_dir() else "") for e in entries)


@tool
def count_files(path: str) -> int:
    "Count the number of files (not directories) directly inside a directory."
    p = Path(path).expanduser()
    if not p.is_dir():
        return 0
    return sum(1 for e in p.iterdir() if e.is_file())


# --- Sub-agent B: knows about math ---
@tool
def calculate(expression: str) -> str:
    "Evaluate a safe arithmetic expression string and return the result."
    allowed = set("0123456789+-*/(). ")
    if not all(c in allowed for c in expression):
        return "Error: unsafe expression."
    return str(eval(expression))  # noqa: S307 — constrained to arithmetic chars above


# Label each sub-agent's events so you can tell them apart in the output.
def make_step_printer(label: str):
    tag = f"[{label.ljust(10)}]"

    def print_step(e: dict):
        event = e["event"]
        if event == "thought":
            print(f"  {tag}[THOUGHT] {str(e.get('content', ''))[:100]}")
        elif event == "action":
            print(
                f"  {tag}[ACTION]  {e.get('tool')} | {json.dumps(e.get('args', {}))[:100]}"
            )
        elif event == "observation":
            print(f"  {tag}[OBS]     {str(e.get('content', ''))[:100]}")
        elif event == "tool_error":
            print(f"  {tag}[ERROR]   {e.get('tool')} — {e.get('error', '')}")
        elif event == "answer":
            print(f"  {tag}[ANSWER]  {str(e.get('content', ''))[:100]}")

    return print_step


async def main():
    async with LLMClient.from_env() as client:
        fs_agent = Agent(
            client=client,
            tools=[list_directory, count_files],
            system_prompt="You are a filesystem assistant. Use the tools to inspect directories.",
            on_event=make_step_printer("FS"),
        )

        math_agent = Agent(
            client=client,
            tools=[calculate],
            system_prompt="You are a calculator. Only perform arithmetic. Use the calculate tool.",
            on_event=make_step_printer("MATH"),
        )

        orchestrator = Orchestrator(
            client=client,
            sub_agents={"filesystem": fs_agent, "math": math_agent},
            on_event=make_step_printer("SUPERVISOR"),
        )

        result = await orchestrator.run(
            "Count the files in ~/Desktop, then multiply that number by 42 and tell me the result."
        )

        print("\n--- ANSWER ---")
        print(result["answer"])
        print(
            f"[tokens] prompt={result['prompt_tokens']} completion={result['completion_tokens']}"
        )


if __name__ == "__main__":
    asyncio.run(main())
