"""Backward-compat re-export. Prefer `llm_framework.core.observability` for new code."""
from llm_framework.core.observability import *  # noqa: F401, F403
from llm_framework.core.observability import (  # private names used by tests
    _attach_ctx,  # noqa: F401
    _context_var,  # noqa: F401
)
