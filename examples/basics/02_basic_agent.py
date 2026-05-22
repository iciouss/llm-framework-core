"""
02 — Basic ReAct Agent

Introduce the Agent class. No tools yet — the agent answers from
its own knowledge. Watch the event callback to see how the framework
emits structured events at each step of the ReAct loop.

New here: Agent, event callback, event shapes.
"""

import asyncio
import json

from llm_framework.core import LLMClient, Agent


# print_event prints every field of every event as raw JSON — useful here
# because the whole point is to see what structure each event carries.
def print_event(e: dict):
    name = e["event"]
    fields = {k: v for k, v in e.items() if k != "event" and "tokens" not in k}
    print(f"  [{name}] {json.dumps(fields, ensure_ascii=False)[:160]}")


async def main():
    async with LLMClient.from_env() as client:
        # system_prompt sets the agent's persistent persona for all run() calls.
        agent = Agent(
            client=client,
            system_prompt="You are a concise assistant. Keep answers to one sentence.",
            on_event=print_event,
        )

        result = await agent.run("What year did the Berlin Wall fall?")

        # result always contains: answer, messages, prompt_tokens, completion_tokens
        print("\n--- ANSWER ---")
        print(result["answer"])
        print(
            f"[tokens] prompt={result['prompt_tokens']} completion={result['completion_tokens']}"
        )


if __name__ == "__main__":
    asyncio.run(main())
