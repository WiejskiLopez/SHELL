"""Kontener infrastruktury messaging (Outbox Relay, Inbox Processor, Publishers)."""
from __future__ import annotations

from dependency_injector import containers, providers

from shell.application.bus.event_bus_publisher import EventBusPublisher
from shell.infrastructure.logging.composite_event_publisher import CompositeEventPublisher
from shell.infrastructure.messaging.outbox_to_inbox_relay import OutboxToInboxRelay
from shell.infrastructure.messaging.processor.inbox_processor import InboxProcessor
from shell.infrastructure.messaging.sql_outbox_publisher import SqlOutboxPublisher
from shell.infrastructure.messaging.worker.messaging_worker import MessagingWorker


class MessagingContainer(containers.DeclarativeContainer):
    """Infrastruktura wzorca Outbox/Inbox - atomowe odpowiedzialności."""

    config = providers.Configuration()
    infra = providers.DependenciesContainer()

    # 1. Publishers (outbound from domain)
    sql_outbox_publisher = providers.Singleton(
        SqlOutboxPublisher,
        session_factory=infra.session_factory,
    )

    # 2. EventBus adapter (inbound to domain handlers)
    bus_publisher = providers.Singleton(
        EventBusPublisher,
        event_bus=providers.Dependency(),  # wired from BusContainer
    )

    # 3. Composite publisher for UoW post-commit (audit + outbox + in-memory bus)
    #    This replaces the one in BusContainer
    event_publisher = providers.Singleton(
        CompositeEventPublisher,
        publishers=providers.List(
            infra.logging_publisher,
            infra.sql_audit_publisher,
            sql_outbox_publisher,      # writes to outbox_event
            bus_publisher,             # fans out to in-memory EventBus
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
        event_publisher=bus_publisher,  # publishes to in-memory EventBus
        batch_size=config.inbox_batch_size,
    )

    # 6. Background Worker (long-running loop for production)


    messaging_worker = providers.Factory(
        MessagingWorker,
        outbox_to_inbox_relay=outbox_to_inbox_relay,
        inbox_processor=inbox_processor,
        poll_interval=config.worker_poll_interval,
        backoff_factor=config.worker_backoff_factor,
        max_backoff=config.worker_max_backoff,
    )