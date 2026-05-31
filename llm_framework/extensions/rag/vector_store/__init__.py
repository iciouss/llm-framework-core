try:
    from .sqlite import SqliteVecBackend

    __all__ = ["SqliteVecBackend"]
except ImportError as _e:
    raise ImportError(
        "SqliteVecBackend requires the [rag] extra: " "pip install 'llm-framework[rag]'"
    ) from _e

try:
    from .qdrant import QdrantBackend

    __all__ = [*globals().get("__all__", []), "QdrantBackend"]
except ImportError as _e:
    raise ImportError(
        "QdrantBackend requires the [qdrant] extra: "
        "pip install 'llm-framework[rag,qdrant]'"
    ) from _e
