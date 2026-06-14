# Canonical exemplar for unit-test-tool. Read before creating a new one.
import pytest

import llm_framework.tools.some_module as mod
from llm_framework.tools.some_module import do_thing, other_thing


@pytest.fixture(autouse=True)
def sandbox(tmp_path, monkeypatch):
    """Redirect module-level safety constants to tmp_path."""
    monkeypatch.setattr(mod, "_SAFE_ROOT", tmp_path)
    return tmp_path


def test_do_thing_happy_path(tmp_path):
    result = do_thing(str(tmp_path / "input.txt"))
    print(f"result: {result!r}")
    assert result == "expected"


def test_do_thing_rejects_unsafe_path(tmp_path):
    with pytest.raises(PermissionError, match="outside allowed root"):
        do_thing(str(tmp_path.parent / "escape.txt"))


def test_output_truncates_at_max(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "_MAX_CHARS", 10)
    result = do_thing(str(tmp_path / "big.txt"))
    assert "truncated" in result


async def test_async_tool_timeout(monkeypatch):
    # ... mock subprocess or async call to trigger timeout ...
    with pytest.raises(TimeoutError):
        await other_thing("input", timeout=0.001)
