---
applyTo: "**"
---

# Development Workflow

Follow this exact workflow for every feature or change request in this repository.

## 1. Plan before touching code

- Read and re-state the request in one sentence to confirm understanding.
- List the files that will be created or modified.
- Identify which documentation locations are affected (see Documentation Scope in `AGENTS.md`).
- Present the plan to the user and wait for confirmation before proceeding.

## 2. Implement following AGENTS.md

Read `AGENTS.md` for all coding rules, architecture conventions, and how-to patterns. Key points:

- Single-line comments only; comments explain _why_, not _what_.
- No block comments, no numbered comments, no emojis.
- Names are provider/backend-agnostic.
- `@tool` and `@mcp.tool()` functions: required full docstring — one-line summary + `Args:` block for every parameter.
- Public methods on services, managers, and protocol interfaces: full docstring when side effects, return shape, or contract are not obvious from the name; otherwise one line.
- Everything else: one line max, or omit when the name is self-explanatory.
- `Returns:` and `Raises:` are optional except on protocol interface methods where they describe the implementor contract.
- Protocol methods must be fully implemented — never stub with `return None`.
- Any pattern introduced in one file of a group (`tools/`, `mcp_servers/`) must be applied to all equivalent files in that group immediately.
- **Adding a dependency:** always use `uv add` (or `uv add --optional <extra>`) — never write version pins by hand. Hand-written pins go stale and introduce security debt.

## 3. Document — update every location that is relevant to the change

Use the Documentation Scope table in `AGENTS.md` to decide what to update. Never skip this step.

Quick reference:

- New file in `core/`, `extensions/`, `tools/`, `mcp_servers/`, or `examples/` → `AGENTS.md` architecture table.
- New user-facing feature or config var → `README.md`.
- New public class or function → docstring + `docs/api/` entry.
- New usage pattern or transport option → `docs/patterns.md`.
- New env var → `.env.example` only (auto-renders to `docs/environment-variables.md`).
- Renamed class/method → grep all doc locations and update every mention.

After each change, run `grep -rn "OldName" docs/ AGENTS.md README.md` to confirm no stale references remain.

## 4. Suggest git commits — do not run them

Before writing any commit message, run `git diff HEAD` to read the actual changes. `git status --short` only lists file names — it is not enough. Bullets must describe WHAT changed as visible in the diff, and WHY it matters. Never write bullets that describe HOW something is implemented, reference session-specific context, or explain things only you and the user know from the current conversation.

Suggest the exact `git add` and `git commit` commands for the user to run after validating. Always include both — never suggest only the commit message. Group ALL uncommitted changes into logical commits — never assume previous changes were already committed.

Commit format (from `AGENTS.md`):

```
type(scope): lowercase imperative subject under 72 chars

- bullet on what changed and why (omit if subject is sufficient)
```

Rules:

- One logical change per commit — never bundle unrelated changes.
- Body only when the subject alone is not enough — short bullet points on WHAT and WHY, not HOW.
- Never `git push` without explicit user instruction.
- Never amend already-pushed commits.
