"""Pure-DI container components and compatibility exports."""

from __future__ import annotations

from shell.platform.bootstrap.container.application import Application
from shell.platform.bootstrap.container.buses import Buses
from shell.platform.bootstrap.container.command_factories import Commands
from shell.platform.bootstrap.container.core_container import Container, CoreContainer
from shell.platform.bootstrap.container.event_handlers import EventHandlers
from shell.platform.bootstrap.container.events import Events
from shell.platform.bootstrap.container.infrastructure import Infrastructure
from shell.platform.bootstrap.container.query_factories import Queries

__all__ = [
	"Application",
	"Buses",
	"Commands",
	"Container",
	"CoreContainer",
	"EventHandlers",
	"Events",
	"Infrastructure",
	"Queries",
]
