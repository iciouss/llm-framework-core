try:
    from qdrant_client import AsyncQdrantClient
    from qdrant_client.models import Distance, PointStruct, VectorParams
except ImportError as _e:
    raise ImportError(
        "QdrantBackend requires the [qdrant] extra: "
        "uv pip install 'llm-framework[qdrant]'"
    ) from _e


class QdrantBackend:
    "Qdrant-based vector storage; supports in-memory, local file, and remote cluster modes."

    # --- construction ---

    def __init__(
        self,
        collection_name: str = "knowledge_base",
        vector_size: int = 768,
        path: str | None = None,
        url: str | None = None,
    ):
        """
        Args:
            collection_name: Qdrant collection to use (default `knowledge_base`).
            vector_size: Dimensionality of embedding vectors; must match the embedding model output (default 768).
            path: Local file path for a persistent on-disk store. Omit for in-memory.
            url: Remote Qdrant cluster URL. Takes precedence over `path`.
        """
        self.collection_name = collection_name
        self.vector_size = vector_size
        self._initialized = False

        if url:
            # remote cluster or cloud
            self.db = AsyncQdrantClient(url=url)
        elif path:
            # local file-backed store, persists across restarts
            self.db = AsyncQdrantClient(path=path)
        else:
            # in-memory, lost on process exit
            self.db = AsyncQdrantClient(location=":memory:")

    # --- internal ---

    async def _ensure_collection(self):
        # lazy because __init__ is sync but collection creation is async
        if not self._initialized:
            if not await self.db.collection_exists(self.collection_name):
                await self.db.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=self.vector_size, distance=Distance.COSINE
                    ),
                )
            self._initialized = True

    # --- storage interface ---

    async def upsert(
        self, ids: list[str], vectors: list[list[float]], payloads: list[dict]
    ):
        await self._ensure_collection()
        points = [
            PointStruct(id=point_id, vector=vector, payload=payload)
            for point_id, vector, payload in zip(ids, vectors, payloads, strict=True)
        ]
        await self.db.upsert(collection_name=self.collection_name, points=points)

    async def search(self, query_vector: list[float], limit: int) -> list[dict]:
        await self._ensure_collection()
        response = await self.db.query_points(
            collection_name=self.collection_name, query=query_vector, limit=limit
        )
        return [hit.payload for hit in response.points]
