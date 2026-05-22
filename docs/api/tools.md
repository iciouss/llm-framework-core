# Built-in Tools

Built-in tools are ready-to-use `@tool` callables that run in-process with the agent.
They are the fastest path to a practical assistant because they require no MCP server setup for local use.

Use these when one script owns the full workflow. Move to MCP servers when tools must be shared across processes.

## Filesystem

Filesystem tools provide safe read/write/list/info operations constrained by the tool's sandbox rules.
Use them for local project analysis, file inspection, and controlled write workflows.

### ::: llm_framework.tools.filesystem

---

## Shell

Shell tools provide controlled command execution with an allowlist-oriented safety model.
Use this when the agent needs CLI capabilities while keeping execution boundaries explicit.

### ::: llm_framework.tools.shell

---

## Web Fetch

Web fetch tools retrieve page content and convert it into model-friendly plain text.
Use them for lightweight retrieval without a full browser automation stack.

### ::: llm_framework.tools.web_fetch

---

## Calculator

Calculator tools provide deterministic arithmetic and avoid model math drift.
Use them whenever numeric correctness matters more than freeform reasoning.

### ::: llm_framework.tools.calculator

---

## Clock

Clock tools provide current UTC date/time information for time-aware responses.
Use them for timestamping, scheduling prompts, and time-window calculations.

### ::: llm_framework.tools.clock

---

## Memory

Memory tool helpers expose a `MemoryStore` instance as agent-callable save/recall/list/delete operations.
Use this when you want memory capabilities without running a separate memory MCP server.

### ::: llm_framework.tools.memory
