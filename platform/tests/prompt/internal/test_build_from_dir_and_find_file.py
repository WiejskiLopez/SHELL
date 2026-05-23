from shell.utils.path.path import PathType
"""Tests for lib/llm_prompt/_build_from_dir.py and lib/llm_prompt/_find_file.py

_build_from_dir: builds structured Markdown from numbered section folders.
find_file: searches input/ then tmp/ for a file by name.
"""

import pytest
from shell.agent_prompt.internal._build_from_dir import _build_from_dir
from shell.agent_prompt.internal._find_file import _find_file


# --- build_from_dir ---

def test_returns_empty_string_for_empty_directory(tmp_path):
    result = _build_from_dir(tmp_path, reader=lambda f: "")
    assert result == ""


def test_builds_heading_from_file_stem(tmp_path):
    (tmp_path / "0001_context.md").write_text("Hello world")
    result = _build_from_dir(tmp_path, reader=lambda f: f.read_text())
    assert "# 1. Context" in result


def test_reader_is_called_for_each_file(tmp_path):
    (tmp_path / "0001_a.md").write_text("A")
    (tmp_path / "0002_b.md").write_text("B")
    seen = []
    def capturing_reader(f):
        seen.append(f.name)
        return ""
    _build_from_dir(tmp_path, reader=capturing_reader)
    assert "0001_a.md" in seen
    assert "0002_b.md" in seen


def test_numeric_prefix_removed_from_heading(tmp_path):
    (tmp_path / "0003_my_task.txt").write_text("content")
    result = _build_from_dir(tmp_path, reader=lambda f: "content")
    assert "0003" not in result
    assert "My task" in result


def test_files_are_ordered_by_name(tmp_path):
    (tmp_path / "0002_bbb.md").write_text("second")
    (tmp_path / "0001_aaa.md").write_text("first")
    result = _build_from_dir(tmp_path, reader=lambda f: f.read_text())
    assert result.index("# 1.") < result.index("# 2.")


# --- find_file ---

def test_find_file_locates_file_in_input(tmp_path):
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "prompt.md").write_text("Hello")
    result = _find_file("prompt.md", tmp_path)
    assert result == input_dir / "prompt.md"


def test_find_file_locates_file_in_tmp_when_not_in_input(tmp_path):
    (tmp_path / "input").mkdir()
    tmp_dir = tmp_path / "temp"
    tmp_dir.mkdir()
    (tmp_dir / "context.txt").write_text("Context")
    result = _find_file("context.txt", tmp_path)
    assert result == tmp_dir / "context.txt"


def test_find_file_returns_none_when_not_found(tmp_path):
    (tmp_path / "input").mkdir()
    (tmp_path / "temp").mkdir()
    result = _find_file("missing.md", tmp_path)
    assert result is None


def test_find_file_prefers_input_over_tmp(tmp_path):
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    tmp_dir = tmp_path / "temp"
    tmp_dir.mkdir()
    (input_dir / "target.md").write_text("from input")
    (tmp_dir / "target.md").write_text("from tmp")
    result = _find_file("target.md", tmp_path)
    assert result == input_dir / "target.md"
