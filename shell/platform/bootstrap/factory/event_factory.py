"""Subscribe event handlers to EventBus.

Cross-BC communication uses source-owned integration events:
each BC defines integration events in its own application layer
(``application/<bc>/<aggregate>/integration_events/``).

The composition root imports from the source BC — this is the only
cross-BC import, and it imports an integration event, not a domain type.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.user.user.integration_events.user_login_succeeded_integration_event import (
    UserLoginSucceededIntegrationEvent,
)

if TYPE_CHECKING:
    from shell.platform.bootstrap.container.core_container import CoreContainer


def register_events(core_container: CoreContainer) -> None:
    """Subscribe all event handlers to the event bus."""
    event_bus = core_container.app.buses.event_bus
    event_handlers = core_container.app.event_handlers

    event_bus.subscribe(
        UserLoginSucceededIntegrationEvent,
        event_handlers.user_login_succeeded_handler_factory,
    )
