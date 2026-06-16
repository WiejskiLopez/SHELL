"""Unit tests for TaskBody value object."""

from __future__ import annotations

import pytest

from shell.domain.value_objects.task_body import TaskBody


class TestTaskBody:
    def test_holds_text_value(self) -> None:
        b = TaskBody("# My Task\n\nSome content")
        assert b.value == "# My Task\n\nSome content"

    def test_str_returns_value(self) -> None:
        b = TaskBody("hello")
        assert str(b) == "hello"

    def test_equality(self) -> None:
        assert TaskBody("a") == TaskBody("a")
        assert TaskBody("a") != TaskBody("b")

    def test_is_hashable(self) -> None:
        s = {TaskBody("x"), TaskBody("x"), TaskBody("y")}
        assert s == {TaskBody("x"), TaskBody("y")}

    @pytest.mark.parametrize("invalid", ["", " ", "\n", "\t", "   \n  "])
    def test_empty_or_whitespace_rejected(self, invalid: str) -> None:
        with pytest.raises(ValueError, match="TaskBody cannot be empty"):
            TaskBody(invalid)

    def test_is_frozen(self) -> None:
        b = TaskBody("x")
        with pytest.raises((AttributeError, Exception)):
            b.value = "y"  # type: ignore[misc]
