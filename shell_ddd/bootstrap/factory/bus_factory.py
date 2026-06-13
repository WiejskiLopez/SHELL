"""Orkiestrator rejestracji szyn — łączy command, query i event registration."""
from __future__ import annotations

from shell_ddd.bootstrap.container.core_container import CoreContainer
from shell_ddd.bootstrap.factory.command_factory import register_commands
from shell_ddd.bootstrap.factory.event_factory import register_events
from shell_ddd.bootstrap.factory.query_factory import register_queries


def wire_buses(core_container: CoreContainer) -> None:
    """Rejestruje wszystkich handlers na CommandBus, QueryBus i EventBus."""
    register_commands(core_container)
    register_queries(core_container)
    register_events(core_container)
