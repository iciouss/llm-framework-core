from datetime import datetime, timezone
from llm_framework.core import tool


@tool
def get_current_datetime() -> str:
    "Return the current UTC date and time in ISO 8601 format."
    return datetime.now(timezone.utc).isoformat()
