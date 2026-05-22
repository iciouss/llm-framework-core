from llm_framework.extensions.auth._context import AuthContext


class MemoryPolicyBackend:
    "In-process policy backend; same rules format as FilePolicyBackend but held in a dict."

    def __init__(self, policy: dict):
        """
        Args:
            policy: Dict with `roles` and `users` keys, matching the FilePolicyBackend JSON schema.
        """
        self._policy = policy

    def _role_tools(self, role: str) -> set[str]:
        return set(self._policy.get("roles", {}).get(role, {}).get("tools", []))

    def get_allowed_tools(self, context: AuthContext) -> set[str]:
        "Effective tool set: union of role grants + extra_tools − denied_tools."
        allowed: set[str] = set()
        for role in context.roles:
            allowed |= self._role_tools(role)
        user_entry = self._policy.get("users", {}).get(context.user_id, {})
        allowed |= set(user_entry.get("extra_tools", []))
        allowed -= set(user_entry.get("denied_tools", []))
        return allowed

    def is_allowed(self, tool_name: str, context: AuthContext) -> bool:
        allowed = self.get_allowed_tools(context)
        return "*" in allowed or tool_name in allowed
