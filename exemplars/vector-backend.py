# Canonical exemplar for vector-backend. Read before creating a new one.
import asyncio

try:
    import some_vector_lib
except ImportError as _e:
    raise ImportError(
        "MyBackend requires the [extra] extra: pip install 'llm-framework[extra]'"
    ) from _e


class MyBackend:
    """Implements BaseStorageBackend Protocol."""

    def __init__(self, path: str = ":memory:", vector_size: int = 768):
        self._path = path
        self._vector_size = vector_size
        self._conn = None

    def _connect(self):
        if self._conn is not None:
            return self._conn
        # ... lazy init: create connection, load extensions, create tables ...
        self._conn = ...
        return self._conn

    async def upsert(
        self, ids: list[str], vectors: list[list[float]], payloads: list[dict]
    ) -> None:
        await asyncio.to_thread(self._upsert_sync, ids, vectors, payloads)

    def _upsert_sync(self, ids, vectors, payloads):
        conn = self._connect()
        ...

    async def search(self, query_vector: list[float], limit: int) -> list[dict]:
        return await asyncio.to_thread(self._search_sync, query_vector, limit)

    def _search_sync(self, query_vector, limit):
        conn = self._connect()
        ...
