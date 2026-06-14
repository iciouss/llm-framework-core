# Canonical exemplar for extension-class. Read before creating a new one.
import asyncio
import os

from llm_framework._env import load_env


class ItemStore:
    """Single-line class description."""

    def __init__(self, path: str | None = None, max_size: int = 1000):
        self._path = path
        self._max_size = max_size
        self._data: dict = {}
        self._lock = asyncio.Lock()

    @classmethod
    def from_env(cls) -> "ItemStore":
        load_env()
        return cls(
            path=os.getenv("ITEM_STORE_PATH"),
            max_size=int(os.getenv("ITEM_STORE_MAX_SIZE", "1000")),
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        pass

    async def save(self, key: str, value: str) -> None:
        async with self._lock:
            ...

    def load(self, key: str) -> str | None:
        ...
