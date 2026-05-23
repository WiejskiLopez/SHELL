from shell.utils.path.path import PathType
"""Tests for shell/agent_prompt/internal/_resolve_prompt.py"""

import pytest
from shell.agent_prompt.internal._resolve_prompt import _resolve_prompt


def test_returns_file_content_for_existing_file_path(tmp_path):
    f = tmp_path / "custom.md"
    f.write_text("custom prompt text")
    result = _resolve_prompt(str(f), tmp_path, reader=lambda p: p.read_text())
    assert result == "custom prompt text"


def test_returns_directory_prompt_for_existing_directory_path(tmp_path):
    prompt_dir = tmp_path / "my_prompts"
    prompt_dir.mkdir()
    (prompt_dir / "0001_intro.md").write_text("Intro content")
    result = _resolve_prompt(str(prompt_dir), tmp_path, reader=lambda p: p.read_text())
    assert "Intro content" in result


def test_plain_text_is_returned_as_is(tmp_path):
    (tmp_path / "input").mkdir()
    (tmp_path / "temp").mkdir()
    result = _resolve_prompt("just plain text here", tmp_path)
    assert result == "just plain text here"


def test_simple_name_resolves_to_file_in_input(tmp_path):
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "task.md").write_text("Task content")
    result = _resolve_prompt("task.md", tmp_path, reader=lambda p: p.read_text())
    assert result == "Task content"


def test_reader_is_used_for_file_reading(tmp_path):
    f = tmp_path / "p.md"
    f.write_text("original")
    result = _resolve_prompt(str(f), tmp_path, reader=lambda p: "injected content")
    assert result == "injected content"
