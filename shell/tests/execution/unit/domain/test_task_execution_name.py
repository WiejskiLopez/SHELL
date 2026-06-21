from __future__ import annotations

import pytest
from shell.domain.execution.value_objects.task_execution_name import TaskExecutionName


class TestTaskExecutionName:
    def test_valid(self) -> None:
        tn = TaskExecutionName("my-task")
        assert str(tn) == "my-task"

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError):
            TaskExecutionName("")

    def test_whitespace_only_raises(self) -> None:
        with pytest.raises(ValueError):
            TaskExecutionName("   ")

    def test_too_long_raises(self) -> None:
        with pytest.raises(ValueError):
            TaskExecutionName("x" * 256)
