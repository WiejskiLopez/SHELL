"""Subscribe event handlers to EventBus."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.bootstrap.platform.container.core_container import CoreContainer


def register_events(core_container: CoreContainer) -> None:
    """Subscribe all event handlers to the event bus."""
    # All complex event handlers have been removed.
    # The event bus is still active for audit logging via the outbox/inbox pipeline.
    pass
