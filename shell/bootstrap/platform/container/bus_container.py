"""Kontener szyn aplikacyjnych (CommandBus, QueryBus, EventBus)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from dependency_injector import containers, providers

if TYPE_CHECKING:
    from dependency_injector.providers import Singleton

    from shell.application.platform.bus.command_bus import CommandBus
    from shell.application.platform.bus.event_bus import EventBus
    from shell.application.platform.bus.query_bus import QueryBus

    class _BusContainerProtocol(Protocol):
        command_bus: Singleton[CommandBus]
        query_bus: Singleton[QueryBus]
        event_bus: Singleton[EventBus]


from shell.application.platform.bus.command_bus import CommandBus
from shell.application.platform.bus.event_bus import EventBus
from shell.application.platform.bus.query_bus import QueryBus
from shell.infrastructure.platform.persistence import SqlAlchemyUnitOfWork


class BusContainer(containers.DeclarativeContainer):
    """Szyny komunikatów oraz fabryka UoW."""

    infra = providers.DependenciesContainer()

    command_bus = providers.Singleton(CommandBus)
    query_bus = providers.Singleton(QueryBus)
    event_bus = providers.Singleton(EventBus)

    uow_factory = providers.Factory(
        SqlAlchemyUnitOfWork,
        session_factory=infra.session_factory,
    )
