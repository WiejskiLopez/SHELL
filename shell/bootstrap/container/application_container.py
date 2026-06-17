"""Kontener aplikacyjny — orkiestruje szyny, komendy, zapytania i eventy."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from dependency_injector import containers, providers

if TYPE_CHECKING:
    from .bus_container import BusContainer
    from .command_container import CommandContainer
    from .event_container import EventContainer
    from .query_container import QueryContainer

    class _ApplicationContainerProtocol(Protocol):
        buses: providers.Container[BusContainer]
        commands: providers.Container[CommandContainer]
        queries: providers.Container[QueryContainer]
        events: providers.Container[EventContainer]

from .bus_container import BusContainer
from .command_container import CommandContainer
from .event_container import EventContainer
from .query_container import QueryContainer


class ApplicationContainer(containers.DeclarativeContainer):
    """Główny kontener aplikacyjny — składa szyny, komendy, zapytania i eventy."""

    config = providers.Configuration()
    infra = providers.DependenciesContainer()
    domain = providers.DependenciesContainer()

    buses: providers.Container[BusContainer] = providers.Container(
        BusContainer,
        infra=infra,
    )

    commands: providers.Container[CommandContainer] = providers.Container(
        CommandContainer,
        config=config,
        infra=infra,
        domain=domain,
        buses=buses,
    )

    queries: providers.Container[QueryContainer] = providers.Container(
        QueryContainer,
        infra=infra,
    )

    events: providers.Container[EventContainer] = providers.Container(
        EventContainer,
        infra=infra,
        domain=domain,
        buses=buses,
    )
