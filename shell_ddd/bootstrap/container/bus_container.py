"""Kontener szyn aplikacyjnych (CommandBus, QueryBus, EventBus) oraz publishera zdarzeń."""
from __future__ import annotations

from dependency_injector import containers, providers

from shell_ddd.application.bus.command_bus import CommandBus
from shell_ddd.application.bus.event_bus import EventBus
from shell_ddd.application.bus.event_bus_publisher import EventBusPublisher
from shell_ddd.application.bus.query_bus import QueryBus
from shell_ddd.infrastructure.logging.composite_event_publisher import CompositeEventPublisher


class BusContainer(containers.DeclarativeContainer):
    """Szyny komunikatów i kompozytowy publisher zdarzeń."""

    infra = providers.DependenciesContainer()

    command_bus = providers.Singleton(CommandBus)
    query_bus = providers.Singleton(QueryBus)
    event_bus = providers.Singleton(EventBus)

    bus_publisher = providers.Singleton(EventBusPublisher, event_bus=event_bus)

    event_publisher = providers.Singleton(
        CompositeEventPublisher,
        publishers=providers.List(
            infra.logging_publisher,
            infra.sql_audit_publisher,
            bus_publisher
        )
    )