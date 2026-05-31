import asyncio
import json
from collections.abc import Callable
from typing import TypedDict

_MAX_CHARS = 20_000


class AgentEvent(TypedDict, total=False):
    "Structured event dict emitted by the agent at each step of the ReAct loop."

    event: str
    prompt: str
    kind: str
    content: str
    step: int
    tool: str
    args: dict
    error: str
    reason: str
    context_tokens: int
    prompt_tokens: int
    completion_tokens: int
    reasoning_tokens: int


class Agent:
    "ReAct agent that iterates tool calls until it reaches a final text answer."

    # --- construction ---

    def __init__(
        self,
        client: object,
        tools: list | None = None,
        max_steps: int = 10,
        max_tokens: int = 4096,
        temperature: float = 0.7,
        max_retries: int = 3,
        system_prompt: str | None = None,
        input_guards: list | None = None,
        output_guards: list | None = None,
        on_event: "Callable[[AgentEvent], object] | None" = None,
        approval_callback: object | None = None,
        approval_tools: list[str] | None = None,
        auth_gate: object | None = None,
    ):
        """
        Args:
            client: An `LLMClient` instance for sending chat completion requests.
            tools: List of `@tool`-decorated callables available during the ReAct loop.
            max_steps: Maximum reasoning iterations before returning a fallback answer (default 10).
            max_tokens: Maximum tokens per LLM response (default 4096). Increase when the model must reproduce large tool results verbatim.
            temperature: Sampling temperature (default 0.7). Use 0.0 for deterministic tasks like structured extraction or KQL generation.
            max_retries: LLM request retry attempts with exponential backoff on 429/5xx errors (default 3).
            system_prompt: Persistent persona injected as the system message on every `run()` call; overridable per-call.
            input_guards: List of callables `(str) -> str` applied to the prompt before the LLM sees it. Raise to block, return to pass/transform.
            output_guards: List of callables `(str) -> str` applied to the final answer. Raise to block, return to pass/transform.
            on_event: Callable receiving structured event dicts at each step. `None` for silent operation.
            approval_callback: Sync or async `(name: str, args: dict) -> bool` called before each tool runs. Return `False` to deny.
            approval_tools: Set of tool names that require approval. If `None`, every tool requires approval.
            auth_gate: An `AuthGate` instance that filters tool schemas and enforces access at execution time. `None` disables auth (all tools allowed).
        """
        self.client = client
        self.max_steps = max_steps
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.max_retries = max_retries
        # stored as the agent's default persona; run() can override per-call
        self.system_prompt = (
            system_prompt or "Solve tasks step-by-step. Use tools when necessary."
        )
        self.tools = tools or []
        # registry maps function name → callable for dispatch during tool calls
        self.registry = {f.__name__: f for f in (tools or [])}
        # schemas is the list of JSON function descriptors sent to the LLM
        self.schemas = [f.schema for f in (tools or []) if hasattr(f, "schema")]
        self.input_guards = input_guards or []
        self.output_guards = output_guards or []
        self.on_event = on_event
        self.approval_callback = approval_callback
        # None means every tool requires approval; a set scopes it to specific names
        self.approval_tools = (
            set(approval_tools) if approval_tools is not None else None
        )
        # None disables auth — all tools are available (backward-compatible default)
        self.auth_gate = auth_gate

    # --- event emission ---

    async def _emit(self, event: dict):
        # supports both sync and async on_event callbacks
        if self.on_event:
            result = self.on_event(event)
            if asyncio.iscoroutine(result):
                await result

    # --- tool validation and execution ---

    def _validate_args(self, name: str, args: dict) -> str | None:
        # skip validation for tools without a schema (e.g. MCP proxies before schema injection)
        func = self.registry.get(name)
        if not func or not hasattr(func, "schema"):
            return None
        params = func.schema["function"]["parameters"]
        required = params.get("required", [])
        missing = [p for p in required if p not in args]
        if missing:
            return f"Missing required arguments for '{name}': {missing}"
        return None

    async def _execute_tool(
        self, name: str, args: dict, auth_context: object | None = None
    ) -> str:
        # registry lookup
        if name not in self.registry:
            error = f"Tool '{name}' not found."
            await self._emit({"event": "tool_error", "tool": name, "error": error})
            return f"Error: {error}"

        # argument validation against the tool's JSON schema
        validation_error = self._validate_args(name, args)
        if validation_error:
            await self._emit(
                {"event": "tool_error", "tool": name, "error": validation_error}
            )
            return f"Error: {validation_error}"

        # execution-time authorization check — defense-in-depth against prompt injection
        if self.auth_gate and not self.auth_gate.authorize(name, auth_context):
            error = f"Access denied: '{name}' is not permitted for this user."
            await self._emit(
                {
                    "event": "tool_error",
                    "tool": name,
                    "error": error,
                    "reason": "access_denied",
                }
            )
            return f"Error: {error}"

        # HITL approval gate — pauses execution until the callback responds
        needs_approval = self.approval_callback and (
            self.approval_tools is None or name in self.approval_tools
        )
        if needs_approval:
            await self._emit(
                {"event": "waiting_for_approval", "tool": name, "args": args}
            )
            approved = self.approval_callback(name, args)
            if asyncio.iscoroutine(approved):
                approved = await approved
            if not approved:
                error = f"Tool '{name}' was denied by the approval callback."
                await self._emit({"event": "tool_error", "tool": name, "error": error})
                return f"Error: {error}"

        # execution — supports both sync and async tools
        try:
            func = self.registry[name]
            result = func(**args)
            if asyncio.iscoroutine(result):
                result = await result
            result = result if isinstance(result, str) else json.dumps(result)
            # truncate large observations so they don't flood the context window
            if len(result) > _MAX_CHARS:
                return (
                    result[:_MAX_CHARS] + "\n...[OBSERVATION TRUNCATED DUE TO LENGTH]"
                )
            return result
        except Exception as e:
            error = str(e)
            await self._emit({"event": "tool_error", "tool": name, "error": error})
            return f"Error executing {name}: {error}"

    async def _run_tool_call(
        self, tc: dict, step: int, tok: dict, auth_context: object | None = None
    ) -> dict:
        # unpack the LLM's tool call request
        fn_name = tc["function"]["name"]
        try:
            fn_args = json.loads(tc["function"]["arguments"])
        except json.JSONDecodeError as exc:
            error = f"Malformed tool arguments from model: {exc}"
            await self._emit({"event": "tool_error", "tool": fn_name, "error": error})
            return {
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": f"Error: {error}",
            }
        # announce the action before executing so the event fires even if the tool raises
        await self._emit(
            {
                "event": "action",
                "step": step + 1,
                "tool": fn_name,
                "args": fn_args,
                **tok,
            }
        )
        observation = await self._execute_tool(fn_name, fn_args, auth_context)
        await self._emit(
            {
                "event": "observation",
                "step": step + 1,
                "tool": fn_name,
                "content": observation,
                **tok,
            }
        )
        # return in the format the OpenAI messages API expects for tool results
        return {
            "role": "tool",
            "tool_call_id": tc["id"],
            "content": observation,
        }

    # --- ReAct loop ---

    async def run(
        self,
        prompt: str,
        system_prompt: str | None = None,
        prior_messages: list[dict] | None = None,
        auth_context: object | None = None,
    ) -> dict:
        """Run the agent on a prompt and return the final answer with cumulative token usage.

        Args:
            prompt: The user's task or question.
            system_prompt: Override the agent's default persona for this call only.
            prior_messages: Previous conversation turns to prepend; use with `HistoryBuffer` for multi-turn conversations.
            auth_context: An `AuthContext` identifying the caller. When combined with `auth_gate`, unauthorized tools are hidden from the LLM and rejected at execution time.

        Returns:
            Dict with keys: `answer` (str), `messages` (list), `context_tokens` (current window size),
            `prompt_tokens` (cumulative billing total), `completion_tokens`, `reasoning_tokens`.
        """

        # input guards run first — they can transform or block the prompt entirely
        system_prompt = system_prompt or self.system_prompt
        for guard in self.input_guards:
            result = guard(prompt)
            if asyncio.iscoroutine(result):
                result = await result
            prompt = result

        # build the initial message list: system + conversation history + new user turn
        messages = (
            [{"role": "system", "content": system_prompt}]
            + (prior_messages or [])
            + [{"role": "user", "content": prompt}]
        )

        await self._emit({"event": "task", "prompt": prompt})

        # accumulators: prompt/completion are cumulative billing totals across all steps;
        # context_tokens reflects only the most recent request's prompt size
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_reasoning_tokens = 0
        context_tokens = 0
        # pre-initialized so the post-loop error path always has a valid tok to spread
        tok = {
            "context_tokens": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "reasoning_tokens": 0,
        }

        for step in range(self.max_steps):
            # --- LLM request ---

            # filter schemas to only tools the caller is authorized to use;
            # unauthorized tools are hidden from the model entirely (not just blocked at execution)
            visible_schemas = (
                self.auth_gate.filter_schemas(self.schemas, auth_context)
                if self.auth_gate
                else self.schemas
            )

            response = await self.client.chat_completions(
                messages,
                tools=visible_schemas or None,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                max_retries=self.max_retries,
            )

            # token accounting: context_tokens = this step's window size, not running total
            usage = response.get("usage", {})
            context_tokens = usage.get("prompt_tokens", 0)
            total_prompt_tokens += context_tokens
            total_completion_tokens += usage.get("completion_tokens", 0)
            total_reasoning_tokens += usage.get("completion_tokens_details", {}).get(
                "reasoning_tokens", 0
            )
            # tok is spread into every emitted event and the final return value
            tok = {
                "context_tokens": context_tokens,
                "prompt_tokens": total_prompt_tokens,
                "completion_tokens": total_completion_tokens,
                "reasoning_tokens": total_reasoning_tokens,
            }

            # --- message processing ---

            msg = response["choices"][0]["message"]
            # strip thinking fields before appending — re-sending them inflates future prompts
            history_msg = {
                k: v
                for k, v in msg.items()
                if k not in ("reasoning_content", "thought", "reasoning")
            }
            messages.append(history_msg)

            # some models return a dedicated reasoning field alongside the response
            reasoning = (
                msg.get("reasoning_content")
                or msg.get("thought")
                or msg.get("reasoning")
            )
            if reasoning:
                await self._emit(
                    {
                        "event": "thought",
                        "kind": "reasoning",
                        "content": reasoning.strip(),
                        **tok,
                    }
                )

            content = msg.get("content") or ""
            tool_calls = msg.get("tool_calls")

            # content alongside tool_calls means the model is narrating its intent ("plan")
            if content and tool_calls:
                await self._emit(
                    {
                        "event": "thought",
                        "kind": "plan",
                        "content": content.strip(),
                        **tok,
                    }
                )

            # --- terminal: no tool calls means the model produced a final answer ---

            if not tool_calls:
                # output guards run last — they can redact or transform the answer
                for guard in self.output_guards:
                    result = guard(content)
                    if asyncio.iscoroutine(result):
                        result = await result
                    content = result
                await self._emit({"event": "answer", "content": content, **tok})
                return {"answer": content, "messages": messages, **tok}

            # --- tool execution (parallel across all tool calls in this step) ---

            tool_messages = await asyncio.gather(
                *[self._run_tool_call(tc, step, tok, auth_context) for tc in tool_calls]
            )
            messages.extend(tool_messages)

        # exhausted max_steps without a final answer
        await self._emit({"event": "error", "reason": "max_steps_reached", **tok})
        return {
            "answer": "(reached maximum steps without a final answer)",
            "messages": messages,
            **tok,
        }
