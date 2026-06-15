"""Kontener szyn aplikacyjnych (CommandBus, QueryBus, EventBus) oraz publishera zdarzeń."""
from __future__ import annotations

from dependency_injector import containers, providers

from shell_ddd.application.bus.command_bus import CommandBus
from shell_ddd.application.bus.event_bus import EventBus
from shell_ddd.application.bus.event_bus_publisher import EventBusPublisher
from shell_ddd.application.bus.query_bus import QueryBus
from shell_ddd.infrastructure.logging.composite_event_publisher import CompositeEventPublisher
from shell_ddd.infrastructure.persistence import SqlAlchemyUnitOfWork
from .messaging_container import MessagingContainer

class BusContainer(containers.DeclarativeContainer):
    """Szyny komunikatów, kompozytowy publisher zdarzeń oraz fabryka UoW
    wstrzykująca publisher post-commit do każdej transakcji."""

    infra = providers.DependenciesContainer()
    messaging = providers.DependenciesContainer()  # NEW

    command_bus = providers.Singleton(CommandBus)
    query_bus = providers.Singleton(QueryBus)
    event_bus = providers.Singleton(EventBus)

    bus_publisher = providers.Singleton(EventBusPublisher, event_bus=event_bus)

    event_publisher = providers.Singleton(
        CompositeEventPublisher,
        publishers=providers.List(
            infra.logging_publisher,
            infra.sql_audit_publisher,
            bus_publisher,
        ),
    )

    # UoW factory wired with the post-commit publisher. Domain events are
    # written to ``outbox_event`` atomically with state inside ``commit()``;
    # the publisher below performs best-effort in-process fan-out *after*
    # the transaction has been durably committed.
    uow_factory = providers.Factory(
        SqlAlchemyUnitOfWork,
        session_factory=infra.session_factory,
        post_commit_publisher=messaging.event_publisher,  # from MessagingContainer
    )