"""Event/command infrastructure container (Event/Command Publishers, Outbox Relay, Inbox Processor)."""

from __future__ import annotations

from dependency_injector import containers, providers

from shell.platform.application.bus.event_bus_publisher import EventBusPublisher
from shell.platform.application.bus.message_bus_publisher import MessageBusPublisher
from shell.platform.infrastructure.messaging.command.command_outbox_to_inbox_relay import (
    CommandOutboxToInboxRelay,
)
from shell.platform.infrastructure.messaging.command.processor.command_inbox_processor import (
    CommandInboxProcessor,
)
from shell.platform.infrastructure.messaging.command.sql_command_outbox_publisher import (
    SqlCommandOutboxPublisher,
)
from shell.platform.infrastructure.messaging.event.event_outbox_to_inbox_relay import (
    EventOutboxToInboxRelay,
)
from shell.platform.infrastructure.messaging.event.processor.event_inbox_processor import (
    EventInboxProcessor,
)
from shell.platform.infrastructure.messaging.event.sql_event_outbox_publisher import (
    SqlEventOutboxPublisher,
)
from shell.platform.infrastructure.messaging.message.message_outbox_to_inbox_relay import (
    MessageOutboxToInboxRelay,
)
from shell.platform.infrastructure.messaging.message.processor.message_inbox_processor import (
    MessageInboxProcessor,
)
from shell.platform.infrastructure.messaging.message.sql_message_outbox_publisher import (
    SqlMessageOutboxPublisher,
)


class EventsContainer(containers.DeclarativeContainer):
    """Outbox/Inbox pattern infrastructure — atomic responsibilities."""

    config = providers.Configuration()
    infra = providers.DependenciesContainer()
    buses = providers.DependenciesContainer()

    # 1. Publishers (outbound from domain)
    sql_event_outbox_publisher = providers.Singleton(
        SqlEventOutboxPublisher,
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

    # 2b. MessageBus adapter (inbound to message handlers)
    message_bus_publisher = providers.Singleton(
        MessageBusPublisher,
        message_bus=buses.message_bus,
    )

    # 3. Outbox Relay (outbox_event → inbox_event)
    event_outbox_to_inbox_relay = providers.Factory(
        EventOutboxToInboxRelay,
        session_factory=infra.session_factory,
        batch_size=config.outbox_batch_size,
    )

    # 5. Inbox Processor (inbox_event → EventBus)
    event_inbox_processor = providers.Factory(
        EventInboxProcessor,
        session_factory=infra.session_factory,
        event_bus=event_bus_publisher,
        batch_size=config.inbox_batch_size,
        max_retries=config.inbox_max_retries,
        retry_backoff_seconds=config.inbox_retry_backoff_seconds,
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

    # 7. Message outbox/inbox
    sql_message_outbox_publisher = providers.Singleton(
        SqlMessageOutboxPublisher,
        session_factory=infra.session_factory,
    )
    message_outbox_to_inbox_relay = providers.Factory(
        MessageOutboxToInboxRelay,
        session_factory=infra.session_factory,
        downstream=message_bus_publisher,
        batch_size=config.outbox_batch_size,
    )
    message_inbox_processor = providers.Factory(
        MessageInboxProcessor,
        session_factory=infra.session_factory,
        message_bus=message_bus_publisher,
        batch_size=config.inbox_batch_size,
        max_retries=config.inbox_max_retries,
        retry_backoff_seconds=config.inbox_retry_backoff_seconds,
    )
