"""
SqliteVecBackend round-trip tests.
No LLM required; uses fixed float vectors.
"""

import asyncio
import math

import pytest

from llm_framework.extensions.rag.vector_store.sqlite import SqliteVecBackend


def cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x**2 for x in a))
    mag_b = math.sqrt(sum(x**2 for x in b))
    return dot / (mag_a * mag_b)


# three orthogonal-ish 3-d vectors
VEC_A = [1.0, 0.0, 0.0]
VEC_B = [0.0, 1.0, 0.0]
VEC_C = [0.0, 0.0, 1.0]
PAYLOAD_A = {"text": "alpha", "source": "test"}
PAYLOAD_B = {"text": "bravo", "source": "test"}
PAYLOAD_C = {"text": "charlie", "source": "test"}


@pytest.fixture
def backend() -> SqliteVecBackend:
    "Fresh in-memory backend for each test."
    return SqliteVecBackend(path=":memory:", vector_size=3)


# --- helpers ---


def run(coro):
    return asyncio.run(coro)


async def _upsert_abc(b: SqliteVecBackend):
    await b.upsert(
        ids=["a", "b", "c"],
        vectors=[VEC_A, VEC_B, VEC_C],
        payloads=[PAYLOAD_A, PAYLOAD_B, PAYLOAD_C],
    )


# --- tests ---


def test_nearest_neighbor_returned_first(backend):
    "Querying with VEC_A should rank 'alpha' highest."
    run(_upsert_abc(backend))
    results = run(backend.search(VEC_A, limit=3))
    assert results[0]["text"] == "alpha"


def test_limit_respected(backend):
    "limit=1 returns exactly one result."
    run(_upsert_abc(backend))
    results = run(backend.search(VEC_A, limit=1))
    assert len(results) == 1


def test_all_payloads_present(backend):
    "All three records survive an upsert and appear in an unlimited search."
    run(_upsert_abc(backend))
    results = run(backend.search(VEC_A, limit=10))
    texts = {r["text"] for r in results}
    assert texts == {"alpha", "bravo", "charlie"}


def test_upsert_replaces_on_same_id(backend):
    "Reinserting the same id must not create a duplicate row."
    run(backend.upsert(["a"], [VEC_A], [PAYLOAD_A]))
    run(backend.upsert(["a"], [VEC_B], [{"text": "alpha-updated"}]))
    results = run(backend.search([0.0, 1.0, 0.0], limit=10))
    # should be exactly one record with id 'a'
    a_records = [r for r in results if r["text"].startswith("alpha")]
    assert len(a_records) == 1
    assert a_records[0]["text"] == "alpha-updated"


def test_empty_store_returns_empty(backend):
    "Search on an empty store returns an empty list."
    results = run(backend.search(VEC_A, limit=5))
    assert results == []


def test_payload_roundtrip(backend):
    "Arbitrary payload keys survive serialisation."
    payload = {"text": "test", "score": 3.14, "tags": ["x", "y"], "nested": {"k": 1}}
    run(backend.upsert(["x"], [VEC_A], [payload]))
    results = run(backend.search(VEC_A, limit=1))
    assert results[0] == payload
