"""Bus registration orchestrator — wires command, query and event registration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.platform.bootstrap.factory.command_factory import register_commands
from shell.platform.bootstrap.factory.event_factory import register_events
from shell.platform.bootstrap.factory.message_factory import register_messages
from shell.platform.bootstrap.factory.query_factory import register_queries

if TYPE_CHECKING:
    from shell.platform.bootstrap.container.core_container import Container


def wire_buses(container: Container) -> None:
    """Rejestruje wszystkich handlers na CommandBus, QueryBus, EventBus i MessageBus."""
    register_commands(container)
    register_queries(container)
    register_events(container)
    register_messages(container)
