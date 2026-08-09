"""Application-layer composition for the root container."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.platform.bootstrap.container.buses import Buses
from shell.platform.bootstrap.container.event_handlers import EventHandlers

if TYPE_CHECKING:
    from shell.platform.bootstrap.container.infrastructure import Infrastructure


class Application:
    """Container for application buses, commands, queries and events."""

    def __init__(self, infra: Infrastructure) -> None:
        from shell.platform.bootstrap.container.command_factories import Commands
        from shell.platform.bootstrap.container.query_factories import Queries

        self.buses = Buses()
        self.commands = Commands(infra=infra)
        self.queries = Queries(infra=infra)
        self.event_handlers = EventHandlers(buses=self.buses, infra=infra)
