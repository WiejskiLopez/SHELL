"""Kontener aplikacyjny — orkiestruje szyny, komendy, zapytania i eventy."""
from __future__ import annotations

from dependency_injector import containers, providers

from .bus_container import BusContainer
from .command_container import CommandContainer
from .event_container import EventContainer
from .query_container import QueryContainer


class ApplicationContainer(containers.DeclarativeContainer):
    """Główny kontener aplikacyjny — składa szyny, komendy, zapytania i eventy."""

    config = providers.Configuration()
    infra = providers.DependenciesContainer()
    domain = providers.DependenciesContainer()
    messaging = providers.DependenciesContainer()  # NEW

    buses = providers.Container(
        BusContainer,
        infra=infra,
        messaging=messaging,  # pass for event_publisher wiring
    )

    commands = providers.Container(
        CommandContainer,
        config=config,
        infra=infra,
        domain=domain,
        buses=buses,
    )

    queries = providers.Container(
        QueryContainer,
        infra=infra,
    )

    events = providers.Container(
        EventContainer,
        infra=infra,
        domain=domain,
        buses=buses,
    )