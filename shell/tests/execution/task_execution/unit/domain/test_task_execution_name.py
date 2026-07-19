from __future__ import annotations

import pytest

from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_name import (
    TaskExecutionName,
)
from shell.platform.domain.exceptions.domain_error import DomainError


class TestTaskExecutionName:
    def test_valid(self) -> None:
        tn = TaskExecutionName("my-task")
        assert str(tn) == "my-task"

    def test_empty_raises(self) -> None:
        with pytest.raises(DomainError):
            TaskExecutionName("")

    def test_whitespace_only_raises(self) -> None:
        with pytest.raises(DomainError):
            TaskExecutionName("   ")

    def test_too_long_raises(self) -> None:
        with pytest.raises(DomainError):
            TaskExecutionName("x" * 256)
