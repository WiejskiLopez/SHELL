from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastapi import Depends
from fastapi import Request as _Request

if TYPE_CHECKING:
    from shell.platform.application.bus.command_bus import CommandBus
    from shell.platform.application.bus.query_bus import QueryBus
    from shell.platform.bootstrap.container.core_container import CoreContainer


def get_core_container(request: _Request) -> CoreContainer:
    return request.app.state.core_container


def _get_buses(container: CoreContainer) -> Any:
    """Zwraca obiekt z .command_bus() / .query_bus() — działa z monolitowym i per-BC kontenerem."""
    if hasattr(container, "app"):
        return container.app.buses
    return container


def get_command_bus(
    container: CoreContainer = Depends(get_core_container),
) -> CommandBus:
    return _get_buses(container).command_bus()  # type: ignore[no-any-return]


def get_query_bus(
    container: CoreContainer = Depends(get_core_container),
) -> QueryBus:
    return _get_buses(container).query_bus()  # type: ignore[no-any-return]
