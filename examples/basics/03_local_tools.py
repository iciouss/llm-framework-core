"""
03 — Agent with Local Tools

Add tools to the agent. The @tool decorator turns any typed function
into an OpenAI-compatible JSON schema automatically. The agent decides
when and which tools to call — you just provide them.

New here: @tool decorator, tools=[...] on Agent.
"""

import asyncio
import json

from llm_framework.core import LLMClient, Agent, tool


# @tool reads the type hints and docstring to generate the JSON schema
# that the LLM uses to understand what each tool does and what it expects.
@tool
def celsius_to_fahrenheit(celsius: float) -> float:
    "Convert a temperature from Celsius to Fahrenheit."
    return celsius * 9 / 5 + 32


@tool
def word_count(text: str) -> int:
    "Count the number of words in a text string."
    return len(text.split())


# Arrow notation makes the call/result pair immediately obvious.
def show_tool_io(e: dict):
    if e["event"] == "action":
        print(
            f"  -> {e.get('tool')}({json.dumps(e.get('args', {}), ensure_ascii=False)[:80]})"
        )
    elif e["event"] == "observation":
        print(f"  <- {str(e.get('content', ''))[:80]}")


async def main():
    async with LLMClient.from_env() as client:
        agent = Agent(
            client=client,
            tools=[celsius_to_fahrenheit, word_count],
            on_event=lambda e: print(
                f"  [{e['event']}] {json.dumps({k: v for k, v in e.items() if k != 'event' and 'tokens' not in k}, ensure_ascii=False)[:160]}"
            ),
        )

        result = await agent.run(
            "What is 22°C in Fahrenheit? Also, how many words are in this sentence: "
            "'The quick brown fox jumps over the lazy dog'?"
        )

        print("\n--- ANSWER ---")
        print(result["answer"])
        print(
            f"[tokens] prompt={result['prompt_tokens']} completion={result['completion_tokens']}"
        )


if __name__ == "__main__":
    asyncio.run(main())
