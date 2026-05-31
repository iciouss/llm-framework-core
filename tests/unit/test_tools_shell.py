import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from llm_framework.tools.shell import _safe_args, _safe_cwd, run_command


def test_disallowed_command_raises():
    with pytest.raises(PermissionError, match="not allowed"):
        asyncio.run(run_command("rm", ["-rf", "/"]))


async def test_allowed_command_not_in_set_raises():
    with pytest.raises(PermissionError):
        await run_command("curl", ["http://example.com"])


def test_safe_cwd_none_returns_home():
    import pathlib

    p = _safe_cwd(None)
    print(f"_safe_cwd(None) = {p}")
    assert p == pathlib.Path.home()


def test_safe_cwd_inside_home_accepted():
    import pathlib

    home = pathlib.Path.home()
    # use the home directory itself as the target — always exists and is within the sandbox
    result = _safe_cwd(str(home))
    print(f"_safe_cwd(home) = {result}")
    assert result == home.resolve()


def test_safe_cwd_outside_home_raises():
    with pytest.raises(PermissionError, match="outside allowed root"):
        _safe_cwd("/etc")


def test_safe_args_absolute_outside_home_raises():
    with pytest.raises(PermissionError, match="outside allowed root"):
        _safe_args(["/etc/passwd"])


def test_safe_args_relative_path_accepted():
    # relative paths are safe — they can't escape cwd
    _safe_args(["relative/path", "another"])


def test_safe_args_empty_accepted():
    _safe_args([])


async def test_run_command_output_truncated(monkeypatch):
    "Output larger than _MAX_CHARS is truncated."
    big_output = b"x" * 25_000

    mock_proc = MagicMock()
    mock_proc.communicate = AsyncMock(return_value=(big_output, b""))

    async def fake_exec(*args, **kwargs):
        return mock_proc

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_exec)
    result = await run_command("echo", ["x"])
    print(f"truncated output length: {len(result)}  ends with: {result[-20:]!r}")
    assert len(result) <= 20_100  # truncated + suffix
    assert "truncated" in result


async def test_run_command_timeout_kills_process(monkeypatch):
    "When the subprocess exceeds the timeout the process is killed and TimeoutError is raised."

    mock_proc = MagicMock()
    mock_proc.kill = MagicMock()
    # second communicate() call (after kill) must succeed
    mock_proc.communicate = AsyncMock(return_value=(b"", b""))

    async def fake_exec(*args, **kwargs):
        return mock_proc

    async def fake_wait_for(coro, timeout):
        coro.close()  # discard the unawaited coroutine to suppress ResourceWarning
        raise asyncio.TimeoutError

    monkeypatch.setattr(asyncio, "create_subprocess_exec", fake_exec)
    monkeypatch.setattr(asyncio, "wait_for", fake_wait_for)

    with pytest.raises(TimeoutError, match="timed out"):
        await run_command("cat", [], timeout=0.001)

    mock_proc.kill.assert_called_once()
