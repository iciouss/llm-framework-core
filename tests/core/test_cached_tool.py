import asyncio
from llm_framework.core import cached_tool


async def main():
    # sync tool is cached — side-effect counter increments only on first call
    call_count = {"n": 0}

    @cached_tool
    def lookup(key: str) -> str:
        "Return a value for a key."
        call_count["n"] += 1
        return f"value:{key}"

    result1 = lookup("foo")
    result2 = lookup("foo")
    assert result1 == result2 == "value:foo"
    assert call_count["n"] == 1, f"expected 1 call, got {call_count['n']}"
    print("sync cached: OK")

    # different args produce different cache entries
    result3 = lookup("bar")
    assert result3 == "value:bar"
    assert call_count["n"] == 2, f"expected 2 calls, got {call_count['n']}"
    print("different args = different entries: OK")

    # async tool is also cached
    async_call_count = {"n": 0}

    @cached_tool
    async def async_lookup(key: str) -> str:
        "Return a value for a key asynchronously."
        async_call_count["n"] += 1
        return f"async:{key}"

    r1 = await async_lookup("x")
    r2 = await async_lookup("x")
    assert r1 == r2 == "async:x"
    assert (
        async_call_count["n"] == 1
    ), f"expected 1 async call, got {async_call_count['n']}"
    print("async cached: OK")

    # LRU eviction: maxsize=2 means the 3rd unique key evicts the least recently used
    lru_count = {"n": 0}

    @cached_tool(maxsize=2)
    def tiny_cache(key: str) -> str:
        "Return a value for a key with tiny LRU cache."
        lru_count["n"] += 1
        return f"v:{key}"

    tiny_cache("a")
    tiny_cache("b")
    count_before = lru_count["n"]
    tiny_cache("c")  # evicts "a" (LRU)
    tiny_cache("a")  # cache miss — must recompute
    assert (
        lru_count["n"] == count_before + 2
    ), f"LRU eviction not working: {lru_count['n']}"
    print("LRU eviction: OK")

    # decorated function retains schema attributes
    assert hasattr(lookup, "schema"), "schema attribute missing"
    assert hasattr(lookup, "name"), "name attribute missing"
    assert hasattr(lookup, "description"), "description attribute missing"
    assert lookup.name == "lookup"
    print("schema attributes retained: OK")

    print("\nAll cached_tool tests passed.")


asyncio.run(main())
