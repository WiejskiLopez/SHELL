"""Unit tests — Faza 11 logging/observability publishers."""
from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

from shell_ddd.domain.events.events import TaskImported, WorkflowStarted
from shell_ddd.domain.value_objects.ids import TaskId, WorkflowId
from shell_ddd.domain.value_objects.task_name import TaskName
from shell_ddd.infrastructure.logging.composite_event_publisher import CompositeEventPublisher
from shell_ddd.infrastructure.logging.logging_event_publisher import LoggingEventPublisher
from shell_ddd.infrastructure.logging.stdlib_logger import (
    JsonFormatter,
    StdlibLogger,
    get_correlation_id,
    set_correlation_id,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _task_imported() -> TaskImported:
    return TaskImported.now(task_id=TaskId.generate(), task_name=TaskName("t1"), now=datetime(2026, 1, 1, tzinfo=UTC))


def _workflow_started() -> WorkflowStarted:
    return WorkflowStarted.now(workflow_id=WorkflowId.generate(), task_name="t1", now=datetime(2026, 1, 1, tzinfo=UTC))


# ---------------------------------------------------------------------------
# StdlibLogger
# ---------------------------------------------------------------------------


def _spy_logger(name: str, level: int = logging.INFO) -> tuple[StdlibLogger, list[logging.LogRecord]]:
    """Return (StdlibLogger, records_list) — records_list is populated on each emit."""
    records: list[logging.LogRecord] = []

    class _Spy(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    logger = StdlibLogger(name, level=level)
    logger._logger.addHandler(_Spy())
    return logger, records


class TestStdlibLogger:
    def test_info_writes_to_logger(self) -> None:
        logger, records = _spy_logger("test_stdlib_info")
        logger.info("hello world")
        assert any("hello world" in r.getMessage() for r in records)

    def test_warning_level(self) -> None:
        logger, records = _spy_logger("test_stdlib_warn")
        logger.warning("watch out")
        assert any(r.levelno == logging.WARNING for r in records)

    def test_error_level(self) -> None:
        logger, records = _spy_logger("test_stdlib_err")
        logger.error("boom")
        assert any(r.levelno == logging.ERROR for r in records)

    def test_debug_level(self) -> None:
        logger, records = _spy_logger("test_stdlib_dbg", level=logging.DEBUG)
        logger.debug("trace")
        assert any(r.levelno == logging.DEBUG for r in records)


class TestJsonFormatter:
    def _make_record(self, msg: str, level: int = logging.INFO) -> logging.LogRecord:
        record = logging.LogRecord(
            name="test", level=level, pathname="", lineno=0, msg=msg, args=(), exc_info=None
        )
        return record

    def test_output_is_valid_json(self) -> None:
        fmt = JsonFormatter()
        record = self._make_record("test message")
        output = fmt.format(record)
        data = json.loads(output)
        assert data["msg"] == "test message"
        assert "ts" in data
        assert "level" in data

    def test_includes_correlation_id(self) -> None:
        set_correlation_id("req-42")
        fmt = JsonFormatter()
        record = self._make_record("msg")
        data = json.loads(fmt.format(record))
        assert data["correlation_id"] == "req-42"
        # cleanup
        set_correlation_id("")

    def test_correlation_id_default_empty(self) -> None:
        set_correlation_id("")
        fmt = JsonFormatter()
        record = self._make_record("msg")
        data = json.loads(fmt.format(record))
        assert data["correlation_id"] == ""


class TestCorrelationId:
    def test_set_and_get(self) -> None:
        set_correlation_id("abc-123")
        assert get_correlation_id() == "abc-123"
        set_correlation_id("")


# ---------------------------------------------------------------------------
# LoggingEventPublisher
# ---------------------------------------------------------------------------


class TestLoggingEventPublisher:
    async def test_logs_each_event(self) -> None:
        spy = MagicMock()
        pub = LoggingEventPublisher(spy)
        events = [_task_imported(), _workflow_started()]
        await pub.publish(events)
        assert spy.info.call_count == 2

    async def test_logs_event_type(self) -> None:
        spy = MagicMock()
        pub = LoggingEventPublisher(spy)
        event = _task_imported()
        await pub.publish([event])
        call_kwargs = spy.info.call_args
        assert call_kwargs.kwargs.get("event_type") == "TaskImported"

    async def test_empty_events_no_log(self) -> None:
        spy = MagicMock()
        pub = LoggingEventPublisher(spy)
        await pub.publish([])
        spy.info.assert_not_called()


# ---------------------------------------------------------------------------
# CompositeEventPublisher
# ---------------------------------------------------------------------------


class TestCompositeEventPublisher:
    async def test_fans_out_to_all_publishers(self) -> None:
        p1 = AsyncMock()
        p2 = AsyncMock()
        p3 = AsyncMock()
        composite = CompositeEventPublisher([p1, p2, p3])
        events = [_task_imported()]
        await composite.publish(events)
        p1.publish.assert_awaited_once_with(events)
        p2.publish.assert_awaited_once_with(events)
        p3.publish.assert_awaited_once_with(events)

    async def test_preserves_order(self) -> None:
        order: list[int] = []

        async def make_mock(n: int) -> object:
            class _Pub:
                async def publish(self, evs: list) -> None:
                    order.append(n)

            return _Pub()

        p1 = await make_mock(1)
        p2 = await make_mock(2)
        composite = CompositeEventPublisher([p1, p2])  # type: ignore[list-item]
        await composite.publish([_task_imported()])
        assert order == [1, 2]

    async def test_empty_publisher_list(self) -> None:
        composite = CompositeEventPublisher([])
        # should not raise
        await composite.publish([_task_imported()])
