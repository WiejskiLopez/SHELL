"""Orkiestrator rejestracji szyn — łączy command, query i event registration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.bootstrap.factory.command_factory import register_commands
from shell.bootstrap.factory.event_factory import register_events
from shell.bootstrap.factory.query_factory import register_queries

if TYPE_CHECKING:
    from shell.bootstrap.container.core_container import CoreContainer


def wire_buses(core_container: CoreContainer) -> None:
    """Rejestruje wszystkich handlers na CommandBus, QueryBus i EventBus."""
    register_commands(core_container)
    register_queries(core_container)
    register_events(core_container)
