"""Unit tests for TaskExecutionBody value object."""

from __future__ import annotations

import pytest

from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_body import (
    TaskExecutionBody,
)


class TestTaskExecutionBody:
    def test_holds_text_value(self) -> None:
        b = TaskExecutionBody("# My Task\n\nSome content")
        assert b.value == "# My Task\n\nSome content"

    def test_str_returns_value(self) -> None:
        b = TaskExecutionBody("hello")
        assert str(b) == "hello"

    def test_equality(self) -> None:
        assert TaskExecutionBody("a") == TaskExecutionBody("a")
        assert TaskExecutionBody("a") != TaskExecutionBody("b")

    def test_is_hashable(self) -> None:
        s = {TaskExecutionBody("x"), TaskExecutionBody("x"), TaskExecutionBody("y")}
        assert s == {TaskExecutionBody("x"), TaskExecutionBody("y")}

    @pytest.mark.parametrize("invalid", ["", " ", "\n", "\t", "   \n  "])
    def test_empty_or_whitespace_rejected(self, invalid: str) -> None:
        with pytest.raises(ValueError, match="TaskExecutionBody cannot be empty"):
            TaskExecutionBody(invalid)

    def test_is_frozen(self) -> None:
        b = TaskExecutionBody("x")
        with pytest.raises((AttributeError, Exception)):
            b.value = "y"  # type: ignore[misc]
