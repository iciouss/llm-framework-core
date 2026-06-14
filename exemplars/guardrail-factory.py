# Canonical exemplar for guardrail-factory. Read before creating a new one.
import re


def block_patterns(patterns: list[str]):
    """Sync guard: raises ValueError on match, returns text unchanged otherwise."""
    compiled = re.compile("|".join(re.escape(p) for p in patterns), re.IGNORECASE)

    def guard(text: str) -> str:
        match = compiled.search(text)
        if match:
            raise ValueError(f"Blocked: '{match.group()}'")
        return text

    return guard


def redact_sensitive():
    """Sync guard: transforms text by replacing sensitive patterns."""
    pattern = re.compile(r"\b\d{3}-\d{3}-\d{4}\b")

    def guard(text: str) -> str:
        return pattern.sub("[REDACTED]", text)

    return guard


def llm_policy_guard(client, policy: str):
    """Async guard: calls an LLM to evaluate text against a policy."""

    async def guard(text: str) -> str:
        response = await client.chat_completions(
            messages=[
                {"role": "system", "content": f"Policy: {policy}. Evaluate the text."},
                {"role": "user", "content": text},
            ],
            temperature=0.0,
        )
        # ... parse structured response, raise ValueError if BLOCK ...
        return text

    return guard
