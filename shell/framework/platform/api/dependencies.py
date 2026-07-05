from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import Depends
from fastapi import Request as _Request

if TYPE_CHECKING:
    from shell.application.platform.bus.command_bus import CommandBus
    from shell.application.platform.bus.query_bus import QueryBus
    from shell.bootstrap.platform.container.core_container import CoreContainer


def get_core_container(request: _Request) -> CoreContainer:
    return request.app.state.core_container


def get_command_bus(
    container: CoreContainer = Depends(get_core_container),
) -> CommandBus:
    return container.app.buses.command_bus()  # type: ignore[attr-defined]


def get_query_bus(
    container: CoreContainer = Depends(get_core_container),
) -> QueryBus:
    return container.app.buses.query_bus()  # type: ignore[attr-defined]
