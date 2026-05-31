import pprint

import pytest

try:
    from llm_framework.extensions.rag.vector_store.sqlite import SqliteVecBackend
except ImportError:
    SqliteVecBackend = None

pytestmark = pytest.mark.skipif(
    SqliteVecBackend is None,
    reason="requires [rag] extra: uv pip install -e '.[rag]'",
)

VEC_A = [1.0, 0.0, 0.0]
VEC_B = [0.0, 1.0, 0.0]
VEC_C = [0.0, 0.0, 1.0]
PAYLOAD_A = {"text": "alpha", "source": "test"}
PAYLOAD_B = {"text": "bravo", "source": "test"}
PAYLOAD_C = {"text": "charlie", "source": "test"}


@pytest.fixture
def backend():
    "Fresh in-memory backend for each test."
    return SqliteVecBackend(path=":memory:", vector_size=3)


async def _upsert_abc(b: SqliteVecBackend):
    await b.upsert(
        ids=["a", "b", "c"],
        vectors=[VEC_A, VEC_B, VEC_C],
        payloads=[PAYLOAD_A, PAYLOAD_B, PAYLOAD_C],
    )


async def test_nearest_neighbor_returned_first(backend):
    "Querying with VEC_A should rank 'alpha' highest."
    await _upsert_abc(backend)
    results = await backend.search(VEC_A, limit=3)
    print("search results (limit=3):")
    pprint.pprint(results)
    assert results[0]["text"] == "alpha"


async def test_limit_respected(backend):
    await _upsert_abc(backend)
    results = await backend.search(VEC_A, limit=1)
    print("search with limit=1:")
    pprint.pprint(results)
    assert len(results) == 1


async def test_all_payloads_present(backend):
    await _upsert_abc(backend)
    results = await backend.search(VEC_A, limit=10)
    texts = {r["text"] for r in results}
    print(f"all texts found: {sorted(texts)}")
    assert texts == {"alpha", "bravo", "charlie"}


async def test_upsert_replaces_on_same_id(backend):
    "Reinserting the same id must not create a duplicate row."
    await backend.upsert(["a"], [VEC_A], [PAYLOAD_A])
    await backend.upsert(["a"], [VEC_B], [{"text": "alpha-updated"}])
    results = await backend.search([0.0, 1.0, 0.0], limit=10)
    a_records = [r for r in results if r.get("text", "").startswith("alpha")]
    print("alpha records after re-upsert:")
    pprint.pprint(a_records)
    assert len(a_records) == 1
    assert a_records[0]["text"] == "alpha-updated"


async def test_empty_store_returns_empty(backend):
    results = await backend.search(VEC_A, limit=5)
    assert results == []


async def test_payload_roundtrip(backend):
    "Arbitrary payload keys survive serialisation."
    payload = {"text": "test", "score": 3.14, "tags": ["x", "y"], "nested": {"k": 1}}
    await backend.upsert(["x"], [VEC_A], [payload])
    results = await backend.search(VEC_A, limit=1)
    print("payload roundtrip:")
    pprint.pprint(results[0])
    assert results[0] == payload


async def test_limit_zero_returns_empty(backend):
    await _upsert_abc(backend)
    results = await backend.search(VEC_A, limit=0)
    assert results == []


async def test_upsert_multiple_then_delete_by_overwrite(backend):
    "A second upsert of the same IDs replaces all three entries without duplicates."
    await _upsert_abc(backend)
    await backend.upsert(
        ["a", "b", "c"],
        [VEC_C, VEC_C, VEC_C],
        [{"text": "a2"}, {"text": "b2"}, {"text": "c2"}],
    )
    results = await backend.search(VEC_C, limit=10)
    texts = {r["text"] for r in results}
    print(f"texts after double upsert: {sorted(texts)}  count: {len(results)}")
    assert texts == {"a2", "b2", "c2"}
    assert len(results) == 3
