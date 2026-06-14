# Canonical exemplar for tool-definition. Read before creating a new one.
from llm_framework.core import tool

_MAX_CHARS = 10_000


@tool
def get_entity(entity_id: str, format: str = "json") -> str:
    """Retrieve an entity by its identifier.

    Args:
        entity_id: Unique identifier for the entity.
        format: Output format (default json).
    """
    ...


@tool
async def process_item(
    name: str,
    tags: list[str] | None = None,
    timeout: float = 30.0,
) -> str:
    """Process an item and return the result.

    Args:
        name: Name of the item to process.
        tags: Optional tags to attach.
        timeout: Maximum seconds to wait (default 30).
    """
    ...
