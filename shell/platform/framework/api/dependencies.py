from __future__ import annotations

from typing import TYPE_CHECKING, Protocol, cast

from fastapi import Depends
from fastapi import Request as _Request

if TYPE_CHECKING:
    from shell.platform.application.bus.command_bus import CommandBus
    from shell.platform.application.bus.query_bus import QueryBus
    from shell.platform.bootstrap.container.core_container import Container


class _BusesProtocol(Protocol):
    command_bus: CommandBus
    query_bus: QueryBus


def get_core_container(request: _Request) -> Container:
    return cast("Container", request.app.state.core_container)


def _get_buses(container: Container) -> _BusesProtocol:
    """Zwraca obiekt z .command_bus / .query_bus — działa z monolitowym i per-BC kontenerem."""
    if hasattr(container, "app"):
        return container.app.buses
    return cast("_BusesProtocol", container)


def get_command_bus(
    container: Container = Depends(get_core_container),
) -> CommandBus:
    return _get_buses(container).command_bus


def get_query_bus(
    container: Container = Depends(get_core_container),
) -> QueryBus:
    return _get_buses(container).query_bus
