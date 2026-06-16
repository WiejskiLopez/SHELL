"""Kontener szyn aplikacyjnych (CommandBus, QueryBus, EventBus)."""

from __future__ import annotations

from dependency_injector import containers, providers

from shell.application.bus.command_bus import CommandBus
from shell.application.bus.event_bus import EventBus
from shell.application.bus.query_bus import QueryBus
from shell.infrastructure.persistence import SqlAlchemyUnitOfWork


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
