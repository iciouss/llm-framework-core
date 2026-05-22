from llm_framework.core.agent import Agent
from llm_framework.core.history import HistoryBuffer
from llm_framework.core.tools import tool


class Orchestrator:
    "Supervisor agent that delegates tasks to named sub-agents via an injected delegate() tool."

    # --- construction ---

    def __init__(
        self,
        client: object,
        sub_agents: dict[str, Agent],
        max_steps: int = 10,
        max_tokens: int = 4096,
        max_retries: int = 3,
        history_max_tokens: int = 8000,
        on_event: object | None = None,
    ):
        """
        Args:
            client: An `LLMClient` instance for the supervisor agent.
            sub_agents: Mapping of agent name to `Agent` instance. Names are exposed to the supervisor as delegation targets.
            max_steps: Maximum supervisor reasoning iterations (default 10).
            max_tokens: Maximum tokens per supervisor response (default 4096).
            max_retries: Retry attempts on transient API errors forwarded to the supervisor agent (default 3).
            history_max_tokens: Token budget for the supervisor history buffer (default 8000).
            on_event: Event callback forwarded to the supervisor agent.
        """
        agents_list = ", ".join(sub_agents.keys())

        # binds sub_agents in closure without module-level state
        @tool
        async def delegate(agent_name: str, task: str) -> str:
            "Delegate a task to a named sub-agent and return its answer."
            if agent_name not in sub_agents:
                return f"Unknown agent '{agent_name}'. Available: {agents_list}"
            agent = sub_agents[agent_name]
            # temporarily wrap on_event to tag events with the delegating agent name
            original_on_event = agent.on_event
            if on_event:
                agent.on_event = lambda e: on_event({**e, "delegated_to": agent_name})
            result = await agent.run(task)
            agent.on_event = original_on_event
            return result.get("answer", "(no answer)")

        self._system_prompt = (
            f"You are a supervisor. Delegate tasks to sub-agents as needed. "
            f"Available agents: {agents_list}."
        )
        self._agent = Agent(
            client,
            tools=[delegate],
            max_steps=max_steps,
            max_tokens=max_tokens,
            max_retries=max_retries,
            on_event=on_event,
        )
        # retains supervisor context across multiple run() calls
        self._history = HistoryBuffer(max_tokens=history_max_tokens)

    async def run(
        self,
        prompt: str,
        system_prompt: str | None = None,
        auth_context: object | None = None,
    ):
        return await self._history.run(
            self._agent,
            prompt,
            system_prompt=system_prompt or self._system_prompt,
            auth_context=auth_context,
        )
