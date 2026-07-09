"""Rejestracja handlerów na MessageBus — wywoływana przez bus_factory.wire_buses()."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.bootstrap.platform.container.core_container import CoreContainer


def register_messages(core_container: CoreContainer) -> None:
    """Rejestruje wszystkie handlery na MessageBus."""
