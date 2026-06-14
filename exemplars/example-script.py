# Canonical exemplar for example-script. Read before creating a new one.
"""
NN — Title of This Example

One-line description of what this example demonstrates.

New here: concept_a, concept_b.
"""
import asyncio

from llm_framework.core import Agent, LLMClient, tool
from llm_framework.observability import set_hook


@tool
def do_something(input: str) -> str:
    """Do something with the input.

    Args:
        input: The input to process.
    """
    ...


class EventPrinter:
    async def emit(self, event):
        if event.event_type == "action":
            print(f"  -> {event.payload.get('tool')}")
        elif event.event_type == "observation":
            print(f"  <- {str(event.payload.get('content', ''))[:80]}")


async def main():
    set_hook(EventPrinter())
    async with LLMClient.from_env() as client:
        agent = Agent(client=client, tools=[do_something])
        result = await agent.run("Do the thing.")

        print("\n--- ANSWER ---")
        print(result["answer"])
        print(f"[tokens] prompt={result['prompt_tokens']} completion={result['completion_tokens']}")


if __name__ == "__main__":
    asyncio.run(main())
