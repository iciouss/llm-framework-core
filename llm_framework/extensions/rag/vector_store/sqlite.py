import asyncio
import json
import sqlite3
from pathlib import Path

try:
    import sqlite_vec
    from sqlite_vec import serialize_float32
except ImportError as _e:
    raise ImportError(
        "SqliteVecBackend requires the [rag] extra: pip install 'llm-framework[rag]'"
    ) from _e


class SqliteVecBackend:
    "SQLite-based vector storage using sqlite-vec; no server required, file or in-memory."

    # --- construction ---

    def __init__(
        self,
        path: str = ":memory:",
        vector_size: int = 768,
    ):
        """
        Args:
            path: SQLite database path. Defaults to ``:memory:`` (lost on process exit).
                  Set to a file path for persistence across restarts.
            vector_size: Dimensionality of embedding vectors; must match the embedding model output (default 768).
        """
        self._path = path
        self._vector_size = vector_size
        self._conn: sqlite3.Connection | None = None

    def _connect(self) -> sqlite3.Connection:
        # lazy init: deferred because __init__ is sync and extension loading is also sync
        if self._conn is not None:
            return self._conn
        if self._path != ":memory:":
            Path(self._path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self._path, check_same_thread=False)
        # python-build-standalone (used by uv) enables load_extension; macOS system Python does not
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id      TEXT PRIMARY KEY,
                embedding BLOB NOT NULL,
                payload TEXT NOT NULL
            )
        """)
        conn.commit()
        self._conn = conn
        return conn

    # --- storage interface ---

    async def upsert(
        self, ids: list[str], vectors: list[list[float]], payloads: list[dict]
    ):
        rows = [
            (id_, serialize_float32(vec), json.dumps(payload))
            for id_, vec, payload in zip(ids, vectors, payloads, strict=True)
        ]
        await asyncio.to_thread(self._upsert_sync, rows)

    def _upsert_sync(self, rows: list[tuple]):
        conn = self._connect()
        conn.executemany(
            "INSERT OR REPLACE INTO chunks(id, embedding, payload) VALUES (?, ?, ?)",
            rows,
        )
        conn.commit()

    async def search(self, query_vector: list[float], limit: int) -> list[dict]:
        return await asyncio.to_thread(self._search_sync, query_vector, limit)

    def _search_sync(self, query_vector: list[float], limit: int) -> list[dict]:
        conn = self._connect()
        rows = conn.execute(
            """
            SELECT payload
            FROM chunks
            ORDER BY vec_distance_cosine(embedding, ?)
            LIMIT ?
            """,
            [serialize_float32(query_vector), limit],
        ).fetchall()
        return [json.loads(row[0]) for row in rows]
