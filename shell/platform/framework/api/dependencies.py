from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

from fastapi import Depends
from fastapi import Request as _Request

if TYPE_CHECKING:
    from dependency_injector.providers import Singleton

    from shell.platform.application.bus.command_bus import CommandBus
    from shell.platform.application.bus.query_bus import QueryBus
    from shell.platform.bootstrap.container.core_container import CoreContainer


class _BusesProtocol(Protocol):
    command_bus: Singleton[CommandBus]
    query_bus: Singleton[QueryBus]


def get_core_container(request: _Request) -> CoreContainer:
    return request.app.state.core_container  # type: ignore[no-any-return]


def _get_buses(container: CoreContainer) -> _BusesProtocol:
    """Zwraca obiekt z .command_bus() / .query_bus() — działa z monolitowym i per-BC kontenerem."""
    if hasattr(container, "app"):
        return container.app.buses  # type: ignore[return-value]
    return container  # type: ignore[return-value]


def get_command_bus(
    container: CoreContainer = Depends(get_core_container),
) -> CommandBus:
    return _get_buses(container).command_bus()  # type: ignore[no-any-return]


def get_query_bus(
    container: CoreContainer = Depends(get_core_container),
) -> QueryBus:
    return _get_buses(container).query_bus()  # type: ignore[no-any-return]
