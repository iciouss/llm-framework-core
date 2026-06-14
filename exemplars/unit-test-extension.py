# Canonical exemplar for unit-test-extension. Read before creating a new one.
from llm_framework.extensions.some_extension import ItemStore


async def test_save_and_load():
    store = ItemStore()
    await store.save("key", "value")
    assert store.load("key") == "value"


async def test_load_missing_returns_none():
    store = ItemStore()
    assert store.load("nope") is None


async def test_delete_removes_entry():
    store = ItemStore()
    await store.save("tmp", "x")
    await store.delete("tmp")
    assert store.load("tmp") is None


async def test_persistence_across_instances(tmp_path):
    path = tmp_path / "data.json"
    store1 = ItemStore(str(path))
    await store1.save("key", "persisted")

    store2 = ItemStore(str(path))
    assert store2.load("key") == "persisted"


async def test_idempotent_delete():
    store = ItemStore()
    await store.delete("never_existed")  # must not raise
