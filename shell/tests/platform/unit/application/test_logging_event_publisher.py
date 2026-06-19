from __future__ import annotations

from unittest.mock import MagicMock

from shell.infrastructure.platform.logging.logging_event_publisher import LoggingEventPublisher
from shell.tests.conftest import _task_imported, _workflow_started


class TestLoggingEventPublisher:
    async def test_logs_each_event(self) -> None:
        spy = MagicMock()
        pub = LoggingEventPublisher(spy)  # type: ignore[arg-type]
        events = [_task_imported(), _workflow_started()]
        await pub.publish(events)
        assert spy.info.call_count == 2

    async def test_logs_event_type(self) -> None:
        spy = MagicMock()
        pub = LoggingEventPublisher(spy)  # type: ignore[arg-type]
        event = _task_imported()
        await pub.publish([event])
        call_kwargs = spy.info.call_args
        assert call_kwargs.kwargs.get("event_type") == "TaskExecutionCreatedEvent"

    async def test_empty_events_no_log(self) -> None:
        spy = MagicMock()
        pub = LoggingEventPublisher(spy)  # type: ignore[arg-type]
        await pub.publish([])
        spy.info.assert_not_called()
