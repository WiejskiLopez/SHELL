"""Kontener infrastruktury eventów/komend (Event/Command Publishers, Outbox Relay, Inbox Processor)."""

from __future__ import annotations

from dependency_injector import containers, providers

from shell.application.platform.bus.event_bus_publisher import EventBusPublisher
from shell.infrastructure.platform.logging.composite_event_publisher import CompositeEventPublisher
from shell.infrastructure.platform.messaging.command.command_outbox_to_inbox_relay import (
    CommandOutboxToInboxRelay,
)
from shell.infrastructure.platform.messaging.command.processor.command_inbox_processor import (
    CommandInboxProcessor,
)
from shell.infrastructure.platform.messaging.command.sql_command_outbox_publisher import (
    SqlCommandOutboxPublisher,
)
from shell.infrastructure.platform.messaging.event.outbox_to_inbox_relay import OutboxToInboxRelay
from shell.infrastructure.platform.messaging.event.processor.inbox_processor import InboxProcessor
from shell.infrastructure.platform.messaging.event.sql_outbox_publisher import SqlOutboxPublisher


class EventsContainer(containers.DeclarativeContainer):
    """Infrastruktura wzorca Outbox/Inbox - atomowe odpowiedzialności."""

    config = providers.Configuration()
    infra = providers.DependenciesContainer()
    buses = providers.DependenciesContainer()

    # 1. Publishers (outbound from domain)
    sql_outbox_publisher = providers.Singleton(
        SqlOutboxPublisher,
        session_factory=infra.session_factory,
    )
    sql_command_outbox_publisher = providers.Singleton(
        SqlCommandOutboxPublisher,
        session_factory=infra.session_factory,
    )

    # 2. EventBus adapter (inbound to domain handlers)
    event_bus_publisher = providers.Singleton(
        EventBusPublisher,
        event_bus=buses.event_bus,
    )

    # 3. Composite publisher for UoW post-commit (audit + outbox + in-memory EventBus)
    event_publisher = providers.Singleton(
        CompositeEventPublisher,
        publishers=providers.List(
            infra.logging_publisher,
            infra.sql_audit_publisher,
            sql_outbox_publisher,
            event_bus_publisher,
        ),
    )

    # 4. Outbox Relay (outbox_event → inbox_event)
    outbox_to_inbox_relay = providers.Factory(
        OutboxToInboxRelay,
        session_factory=infra.session_factory,
        batch_size=config.outbox_batch_size,
    )

    # 5. Inbox Processor (inbox_event → EventBus)
    inbox_processor = providers.Factory(
        InboxProcessor,
        session_factory=infra.session_factory,
        event_publisher=event_bus_publisher,
        batch_size=config.inbox_batch_size,
    )

    # 6. Command outbox/inbox
    command_outbox_to_inbox_relay = providers.Factory(
        CommandOutboxToInboxRelay,
        session_factory=infra.session_factory,
        batch_size=config.command_outbox_batch_size,
    )
    command_inbox_processor = providers.Factory(
        CommandInboxProcessor,
        session_factory=infra.session_factory,
        command_bus=buses.command_bus,
        batch_size=config.command_inbox_batch_size,
    )
