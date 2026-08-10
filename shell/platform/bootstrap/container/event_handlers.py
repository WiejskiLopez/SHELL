"""Application event handler factories."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.platform.bootstrap.container.buses import Buses
    from shell.platform.bootstrap.container.infrastructure import Infrastructure


class EventHandlers:
    """Container for event handler factories."""

    def __init__(self, buses: Buses, infra: Infrastructure) -> None:
        self._buses = buses
        self._infra = infra
