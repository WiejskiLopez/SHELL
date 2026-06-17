"""Unit tests for domain value objects."""

from __future__ import annotations

from datetime import UTC

import pytest

from shell.domain.value_objects.hash import Hash
from shell.domain.value_objects.ids import EnvelopeId, TaskExecutionId, WorkflowId
from shell.domain.value_objects.mode import Mode
from shell.domain.value_objects.status import Status
from shell.domain.value_objects.task_execution_name import TaskExecutionName
from shell.domain.value_objects.timestamp import Timestamp


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


class TestHash:
    def test_of_string(self) -> None:
        h = Hash.of("hello")
        assert len(h.value) == 64

    def test_deterministic(self) -> None:
        assert Hash.of("abc") == Hash.of("abc")

    def test_different_inputs(self) -> None:
        assert Hash.of("abc") != Hash.of("xyz")

    def test_invalid_length(self) -> None:
        with pytest.raises(ValueError):
            Hash("short")

    def test_invalid_hex(self) -> None:
        with pytest.raises(ValueError):
            Hash("z" * 64)


class TestIds:
    def test_task_execution_id_generate(self) -> None:
        t1 = TaskExecutionId.generate()
        t2 = TaskExecutionId.generate()
        assert t1 != t2
        assert len(t1.value) == 36  # UUID4

    def test_task_execution_id_empty_raises(self) -> None:
        with pytest.raises(ValueError):
            TaskExecutionId("")

    def test_workflow_id_generate(self) -> None:
        w = WorkflowId.generate()
        assert w.value

    def test_envelope_id_generate(self) -> None:
        e = EnvelopeId.generate()
        assert e.value


class TestMode:
    def test_values(self) -> None:
        assert Mode.AGENT.value == "agent"
        assert Mode.ROUTER.value == "router"

    def test_str_enum(self) -> None:
        assert Mode("worker") == Mode.WORKER


class TestStatus:
    def test_sentinels(self) -> None:
        assert Status.idle().value == "idle"
        assert Status.running().value == "running"
        assert Status.done().value == "done"
        assert Status.failed().value == "failed"

    def test_empty_raises(self) -> None:
        with pytest.raises(ValueError):
            Status("")


class TestTimestamp:
    def test_now_is_utc(self) -> None:

        ts = Timestamp.now()
        assert ts.value.tzinfo == UTC

    def test_naive_raises(self) -> None:
        from datetime import datetime

        with pytest.raises(ValueError):
            Timestamp(datetime(2024, 1, 1))  # naive
