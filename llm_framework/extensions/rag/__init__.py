import logging
import os
import uuid
from pathlib import Path
from typing import Protocol, runtime_checkable

from ._converter import to_markdown

log = logging.getLogger(__name__)

try:
    from semantic_text_splitter import MarkdownSplitter as _MarkdownSplitter
except ImportError:
    _MarkdownSplitter = None  # type: ignore[assignment]


@runtime_checkable
class BaseStorageBackend(Protocol):
    "Interface for vector database backends."

    async def upsert(
        self, ids: list[str], vectors: list[list[float]], payloads: list[dict]
    ): ...

    async def search(self, query_vector: list[float], limit: int) -> list[dict]: ...


def backend_from_env(collection: str | None = None) -> BaseStorageBackend:
    """Construct the configured vector backend from environment variables.

    Args:
        collection: Optional logical name for the vector namespace (collection or database).
            When provided, backends use it to isolate data — sqlite appends it as
            ``<SQLITE_PATH>/<collection>.db``; qdrant uses it as the collection name.
            When omitted, each backend falls back to its own env-var default.
    """
    name = os.getenv("VECTOR_BACKEND", "sqlite").lower()

    if name == "sqlite":
        from llm_framework.extensions.rag.vector_store.sqlite import SqliteVecBackend

        if collection:
            base = os.getenv("SQLITE_PATH", "./data/sqlite")
            path = str(Path(base) / f"{collection}.db")
        else:
            path = os.getenv("SQLITE_PATH", ":memory:")

        return SqliteVecBackend(
            path=path,
            vector_size=int(os.getenv("VECTOR_SIZE", "768")),
        )

    if name == "qdrant":
        from llm_framework.extensions.rag.vector_store.qdrant import QdrantBackend

        return QdrantBackend(
            collection_name=collection
            or os.getenv("QDRANT_COLLECTION", "knowledge_base"),
            vector_size=int(os.getenv("VECTOR_SIZE", "768")),
            path=os.getenv("QDRANT_PATH"),
            url=os.getenv("QDRANT_URL"),
        )

    raise ValueError(f"Unknown VECTOR_BACKEND: '{name}'")


class RAGStore:
    "Retrieval-augmented generation store: ingest files and search by semantic similarity."

    def __init__(
        self,
        llm_client: object,
        storage_backend: BaseStorageBackend,
        default_max_tokens: int = 300,
        embed_batch_size: int = 64,
        _owns_client: bool = False,
    ):
        """
        Args:
            llm_client: An `LLMClient` instance used exclusively for embedding requests.
            storage_backend: A `BaseStorageBackend` implementation (e.g. `QdrantBackend`).
            default_max_tokens: Approximate token limit per chunk when ingesting files (default 300).
            embed_batch_size: Maximum strings per embedding API call; prevents exceeding provider limits (default 64).
        """
        self.llm = llm_client
        self.storage = storage_backend
        self.default_max_tokens = default_max_tokens
        self._embed_batch_size = embed_batch_size
        self._owns_client = _owns_client
        if _MarkdownSplitter is None:
            raise ImportError(
                "RAGStore requires the [rag] extra: "
                "uv pip install 'llm-framework[rag]'"
            )

    @classmethod
    def from_env(cls, storage_backend: BaseStorageBackend) -> "RAGStore":
        "Construct a RAGStore from env vars; must be used as an async context manager to avoid leaking the HTTP client."
        from llm_framework.core.llm import LLMClient
        from dotenv import find_dotenv, load_dotenv

        load_dotenv(find_dotenv(usecwd=True), override=True)
        client = LLMClient(
            base_url=os.environ["LLM_BASE_URL"],
            api_key=os.environ["LLM_API_KEY"],
            model=os.getenv("EMBED_MODEL", os.environ["LLM_MODEL"]),
            verify=os.getenv("CA_BUNDLE_PATH") or True,
        )
        return cls(client, storage_backend, _owns_client=True)

    # --- lifecycle ---

    async def __aenter__(self):
        if self._owns_client:
            await self.llm.__aenter__()
        return self

    async def __aexit__(self, *exc):
        if self._owns_client:
            await self.llm.__aexit__(*exc)

    # --- operations ---

    async def ingest_file(self, file_path: str | Path, max_tokens: int | None = None):
        "Convert, chunk, embed, and store a file; returns the number of chunks ingested."
        path_obj = Path(file_path)

        # sandbox to home directory so library callers can't read arbitrary filesystem paths
        try:
            path_obj.resolve().relative_to(Path.home())
        except ValueError:
            raise PermissionError(
                f"Path '{path_obj.resolve()}' is outside the home directory sandbox"
            )

        if not path_obj.exists():
            raise FileNotFoundError(f"Cannot find file: {file_path}")

        try:
            text_content = to_markdown(path_obj)
        except Exception as exc:
            log.warning("Failed to extract text from %s: %s", file_path, exc)
            return 0

        if not text_content or not text_content.strip():
            return 0

        limit = max_tokens if max_tokens is not None else self.default_max_tokens
        overlap_limit = int(limit * 0.15)

        # char÷4 approximates tokens without a tokenizer
        splitter = _MarkdownSplitter.from_callback(
            lambda text: len(text) // 4, limit, overlap=overlap_limit
        )
        chunks = splitter.chunks(text_content)

        if not chunks:
            return 0

        # batch calls to stay within provider per-request token limits
        vectors: list[list[float]] = []
        for i in range(0, len(chunks), self._embed_batch_size):
            batch = chunks[i : i + self._embed_batch_size]
            vectors.extend(await self.llm.embeddings(batch))
        # deterministic UUIDs make re-ingestion idempotent and satisfy Qdrant point id format
        ids = [
            str(uuid.uuid5(uuid.NAMESPACE_URL, f"{path_obj.name}:{chunk}"))
            for chunk in chunks
        ]
        payloads = [{"text": chunk, "source": path_obj.name} for chunk in chunks]

        await self.storage.upsert(ids, vectors, payloads)
        return len(chunks)

    async def search(self, query: str, limit: int = 3):
        "Return the top-k most semantically similar passages for a query string."
        query_vector = (await self.llm.embeddings([query]))[0]
        payloads = await self.storage.search(query_vector, limit)
        return [
            f"Source: {payload.get('source', 'Unknown')}\n\n{payload.get('text', '')}"
            for payload in payloads
        ]
