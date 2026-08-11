from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, cast

from fastapi import Depends
from fastapi import Request as _Request

if TYPE_CHECKING:
    from shell.platform.application.bus.command_bus import CommandBus
    from shell.platform.application.bus.query_bus import QueryBus


class _BusesProtocol(Protocol):
    command_bus: CommandBus
    query_bus: QueryBus


class ContainerProtocol(Protocol):
    """Minimal platform-neutral shape exposed to framework dependencies."""

    app: Any
    infra: Any


def get_core_container(request: _Request) -> ContainerProtocol:
    return cast("ContainerProtocol", request.app.state.core_container)


def _get_buses(container: ContainerProtocol) -> _BusesProtocol:
    """Zwraca obiekt z .command_bus / .query_bus — działa z monolitowym i per-BC kontenerem."""
    if hasattr(container, "app"):
        return container.app.buses
    return cast("_BusesProtocol", container)


def get_command_bus(
    container: ContainerProtocol = Depends(get_core_container),
) -> CommandBus:
    bus = _get_buses(container).command_bus
    if not hasattr(bus, "dispatch") and callable(bus):
        bus = bus()
    return cast("CommandBus", bus)


def get_query_bus(
    container: ContainerProtocol = Depends(get_core_container),
) -> QueryBus:
    bus = _get_buses(container).query_bus
    if not hasattr(bus, "dispatch") and callable(bus):
        bus = bus()
    return cast("QueryBus", bus)
