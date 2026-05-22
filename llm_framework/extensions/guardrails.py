import re
import json

_POLICY_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "policy_evaluation",
        "strict": True,  # prevents the model from returning undeclared fields
        "schema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "enum": ["ALLOW", "BLOCK"],
                    "description": "The final decision. Must be ALLOW or BLOCK.",
                },
                "reason": {
                    "type": "string",
                    "description": "A short reason for the violation. Leave as an empty string if ALLOW.",
                },
            },
            "required": ["status", "reason"],
            "additionalProperties": False,
        },
    },
}


def block_keywords(words: list[str]):
    "Return a guard that raises if any blocked keyword appears in the text (case-insensitive)."
    pattern = re.compile("|".join(re.escape(w) for w in words), re.IGNORECASE)

    def guard(text: str) -> str:
        match = pattern.search(text)
        if match:
            raise ValueError(f"Blocked keyword detected: '{match.group()}'")
        return text

    return guard


def strip_pii():
    "Return a guard that replaces email addresses and phone numbers with redaction placeholders."
    # covers common email and phone patterns only
    email = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
    phone = re.compile(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b")

    def guard(text: str) -> str:
        text = email.sub("[EMAIL]", text)
        text = phone.sub("[PHONE]", text)
        return text

    return guard


def llm_guard(client, policy: str):
    """Return an async guard that evaluates text against a natural language policy using an LLM.

    Requires a provider that supports structured output (json_schema response_format with strict=True).
    """

    # LLM evaluation catches contextual violations regex misses
    async def guard(text: str) -> str:
        response = await client.chat_completions(
            messages=[
                {
                    "role": "system",
                    "content": (
                        f"You are a content policy enforcer. Policy: {policy}\n"
                        "Evaluate the user's text against the policy.\n"
                        "Respond with status=ALLOW if the text complies and should be permitted.\n"
                        "Respond with status=BLOCK if the text violates the policy and should be rejected.\n"
                        "Provide a short reason only when blocking; leave reason empty when allowing."
                    ),
                },
                # XML tags prevent the evaluated text from being injected as instructions
                {"role": "user", "content": f"<evaluate>{text}</evaluate>"},
            ],
            temperature=0.0,
            max_tokens=50,
            response_format=_POLICY_SCHEMA,
        )
        verdict = response["choices"][0]["message"]["content"]
        verdict_data = json.loads(verdict)
        if verdict_data["status"].upper() == "BLOCK":
            raise ValueError(f"Guard blocked: {verdict_data['reason']}")
        return text

    return guard
