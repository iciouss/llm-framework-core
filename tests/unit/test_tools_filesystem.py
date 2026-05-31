import pytest

import llm_framework.tools.filesystem as fs_module
from llm_framework.tools.filesystem import (
    file_info,
    list_directory,
    read_file,
    write_file,
)


@pytest.fixture(autouse=True)
def sandbox(tmp_path, monkeypatch):
    "Redirect _SAFE_ROOT to tmp_path so tests never touch real home directories."
    monkeypatch.setattr(fs_module, "_SAFE_ROOT", tmp_path)
    return tmp_path


def test_write_then_read_roundtrip(tmp_path):
    p = tmp_path / "hello.txt"
    write_file(str(p), "hello world")
    result = read_file(str(p))
    print(f"read_file: {result!r}")
    assert result == "hello world"


def test_write_creates_parent_dirs(tmp_path):
    p = tmp_path / "sub" / "deep" / "file.txt"
    write_file(str(p), "nested")
    assert p.exists()
    assert p.read_text() == "nested"


def test_read_file_path_traversal_raises(tmp_path):
    outside = tmp_path.parent / "outside.txt"
    with pytest.raises(PermissionError, match="outside allowed root"):
        read_file(str(outside))


def test_write_file_path_traversal_raises(tmp_path):
    outside = tmp_path.parent / "evil.txt"
    with pytest.raises(PermissionError, match="outside allowed root"):
        write_file(str(outside), "evil")


def test_list_directory_returns_entries(tmp_path):
    (tmp_path / "alpha.txt").write_text("a")
    (tmp_path / "beta.txt").write_text("b")
    (tmp_path / "sub").mkdir()
    entries = list_directory(str(tmp_path))
    print(f"list_directory entries: {entries}")
    assert "alpha.txt" in entries
    assert "beta.txt" in entries
    assert "sub/" in entries


def test_list_directory_sorted(tmp_path):
    for name in ["c.txt", "a.txt", "b.txt"]:
        (tmp_path / name).write_text(name)
    entries = list_directory(str(tmp_path))
    print(f"sorted entries: {entries}")
    assert entries == sorted(entries)


def test_list_directory_path_traversal_raises(tmp_path):
    outside = tmp_path.parent
    with pytest.raises(PermissionError, match="outside allowed root"):
        list_directory(str(outside))


def test_list_directory_non_dir_raises(tmp_path):
    p = tmp_path / "file.txt"
    p.write_text("hi")
    with pytest.raises(NotADirectoryError):
        list_directory(str(p))


def test_file_info_returns_correct_type_file(tmp_path):
    p = tmp_path / "data.txt"
    p.write_text("content")
    info = file_info(str(p))
    print(f"file_info(file): {info}")
    assert info["type"] == "file"
    assert info["size_bytes"] == len("content")


def test_file_info_returns_correct_type_dir(tmp_path):
    info = file_info(str(tmp_path))
    print(f"file_info(dir): {info}")
    assert info["type"] == "directory"


def test_file_info_path_traversal_raises(tmp_path):
    outside = tmp_path.parent
    with pytest.raises(PermissionError, match="outside allowed root"):
        file_info(str(outside))


def test_read_file_truncates_at_max_chars(tmp_path, monkeypatch):
    monkeypatch.setattr(fs_module, "_MAX_CHARS", 10)
    p = tmp_path / "big.txt"
    p.write_text("x" * 50)
    result = read_file(str(p))
    print(f"truncated result: {result!r}")
    assert result.endswith("...[truncated]")
    assert len(result) < 50
