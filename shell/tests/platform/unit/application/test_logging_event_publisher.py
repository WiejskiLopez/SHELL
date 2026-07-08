from __future__ import annotations

from typing import TYPE_CHECKING, cast
from unittest.mock import MagicMock

from shell.infrastructure.platform.logging.logging_event_publisher import LoggingEventPublisher
from shell.tests.shared.sample_aggregate import make_sample_event

if TYPE_CHECKING:
    from shell.domain.platform.events import DomainEvent


class TestLoggingEventPublisher:
    async def test_logs_each_event(self) -> None:
        spy = MagicMock()
        pub = LoggingEventPublisher(spy)
        events = cast("list[DomainEvent]", [make_sample_event(), make_sample_event()])
        await pub.publish(events)
        assert spy.info.call_count == 2

    async def test_logs_event_type(self) -> None:
        spy = MagicMock()
        pub = LoggingEventPublisher(spy)
        event = make_sample_event()
        await pub.publish(cast("list[DomainEvent]", [event]))
        call_kwargs = spy.info.call_args
        assert call_kwargs.kwargs.get("event_type") == "_SampleEvent"

    async def test_empty_events_no_log(self) -> None:
        spy = MagicMock()
        pub = LoggingEventPublisher(spy)
        await pub.publish([])
        spy.info.assert_not_called()
