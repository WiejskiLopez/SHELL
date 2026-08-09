"""Root composition container."""

from __future__ import annotations

from typing import Any

from shell.infrastructure.scheduling.services.scheduler_service import SchedulerService
from shell.platform.bootstrap.container.application import Application
from shell.platform.bootstrap.container.events import Events
from shell.platform.bootstrap.container.infrastructure import Infrastructure


class Container:
    """Root Pure DI container composing infrastructure and application layers."""

    def __init__(
        self,
        db_url: str = "",
        events_config: dict[str, Any] | None = None,
    ) -> None:
        self.infra = Infrastructure(db_url=db_url)
        self.app = Application(infra=self.infra)
        self.events = Events(
            infra=self.infra,
            buses=self.app.buses,
            events_config=events_config,
        )
        self.scheduler_service = SchedulerService(
            session_factory=self.infra.session_factory,
            event_outbox_to_inbox_relay=self.events.event_outbox_to_inbox_relay,  # type: ignore[arg-type]
            event_inbox_processor=self.events.event_inbox_processor,  # type: ignore[arg-type]
            message_outbox_to_inbox_relay=self.events.message_outbox_to_inbox_relay,  # type: ignore[arg-type]
            message_inbox_processor=self.events.message_inbox_processor,  # type: ignore[arg-type]
        )


CoreContainer = Container
