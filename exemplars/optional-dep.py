# Canonical exemplar for optional-dep. Read before creating a new one.
from llm_framework._optional import require as _require

try:
    from expensive_library import ExpensiveClient
except ImportError:
    ExpensiveClient = None  # type: ignore[misc,assignment]

try:
    from another_library import AnotherThing
except ImportError:
    AnotherThing = None  # type: ignore[misc,assignment]


class FeatureThatNeedsIt:
    def __init__(self, client):
        _require("expensive_library", ExpensiveClient)
        self._client = client
