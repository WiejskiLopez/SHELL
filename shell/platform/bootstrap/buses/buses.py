"""Application bus container."""

from __future__ import annotations

from shell.platform.application.bus.command_bus import CommandBus
from shell.platform.application.bus.event_bus import EventBus
from shell.platform.application.bus.query_bus import QueryBus


class Buses:
    """Container for application buses shared across the system."""

    def __init__(self) -> None:
        self.command_bus = CommandBus()
        self.query_bus = QueryBus()
        self.event_bus = EventBus()
