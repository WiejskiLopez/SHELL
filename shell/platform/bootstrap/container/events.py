"""Event and message transport dependencies for the root container."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.platform.application.bus.event_bus_publisher import EventBusPublisher
from shell.platform.application.bus.message_bus_publisher import MessageBusPublisher
from shell.platform.infrastructure.messaging.event.event_outbox_to_inbox_relay import (
    EventOutboxToInboxRelay,
)
from shell.platform.infrastructure.messaging.event.processor.event_inbox_processor import (
    EventInboxProcessor,
)
from shell.platform.infrastructure.messaging.message.message_outbox_to_inbox_relay import (
    MessageOutboxToInboxRelay,
)
from shell.platform.infrastructure.messaging.message.processor.message_inbox_processor import (
    MessageInboxProcessor,
)
from shell.platform.infrastructure.serialization.event_registry import build_event_registry
from shell.platform.infrastructure.serialization.message_registry import build_message_registry

if TYPE_CHECKING:
    from shell.platform.bootstrap.container.buses import Buses
    from shell.platform.bootstrap.container.infrastructure import Infrastructure


class Events:
    """Container for event and message outbox/inbox infrastructure."""

    def __init__(
        self,
        infra: Infrastructure,
        buses: Buses,
        events_config: dict[str, Any] | None = None,
    ) -> None:
        event_config = events_config or {}
        self._infra = infra
        self._buses = buses
        self._event_registry = build_event_registry()
        self._event_bus_publisher = EventBusPublisher(event_bus=buses.event_bus)
        self._message_registry = build_message_registry()
        self._message_bus_publisher = MessageBusPublisher(message_bus=buses.message_bus)
        self._outbox_batch_size = event_config.get("outbox_batch_size", 100)
        self._inbox_batch_size = event_config.get("inbox_batch_size", 50)
        self._command_outbox_batch_size = event_config.get("command_outbox_batch_size", 100)
        self._command_inbox_batch_size = event_config.get("command_inbox_batch_size", 50)

    def event_outbox_to_inbox_relay(self) -> EventOutboxToInboxRelay:
        return EventOutboxToInboxRelay(
            session_factory=self._infra.session_factory,
            downstream=self._event_bus_publisher,
            batch_size=self._outbox_batch_size,
        )

    def event_inbox_processor(self) -> EventInboxProcessor:
        return EventInboxProcessor(
            session_factory=self._infra.session_factory,
            event_bus=self._event_bus_publisher,
            batch_size=self._inbox_batch_size,
            registry=self._event_registry,
        )

    def message_outbox_to_inbox_relay(self) -> MessageOutboxToInboxRelay:
        return MessageOutboxToInboxRelay(
            session_factory=self._infra.session_factory,
            downstream=self._message_bus_publisher,
            batch_size=self._outbox_batch_size,
        )

    def message_inbox_processor(self) -> MessageInboxProcessor:
        return MessageInboxProcessor(
            session_factory=self._infra.session_factory,
            message_bus=self._message_bus_publisher,
            batch_size=self._inbox_batch_size,
            registry=self._message_registry,
        )
