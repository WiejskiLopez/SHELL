from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from shell.platform.application.command_handlers.command_handler import CommandHandler
from shell.platform.application.context.causation_id import get_causation_id
from shell.platform.application.context.correlation_id import get_or_create_correlation_id
from shell.project_service.application.project.project_provision.commands.release_workspace_command import (
    ReleaseWorkspaceCommand,
)
from shell.project_service.application.project.project_provision.integration_events.workspace_released_integration_event import (
    WorkspaceReleasedIntegrationEvent,
)

if TYPE_CHECKING:
    from shell.platform.application.ports.messaging.event_publisher import EventPublisher


class ReleaseWorkspaceHandler(CommandHandler[ReleaseWorkspaceCommand]):
    """Kompensacja pilota — publikuje fakt zwolnienia workspace'u."""

    def __init__(self, event_publisher: EventPublisher) -> None:
        self._event_publisher = event_publisher

    async def handle(self, command: ReleaseWorkspaceCommand) -> None:
        event = WorkspaceReleasedIntegrationEvent(
            event_id=str(uuid.uuid4()),
            correlation_id=get_or_create_correlation_id(),
            causation_id=get_causation_id(),
            occurred_at=datetime.now(tz=UTC),
            aggregate_id=command.project_id,
            schema_version=1,
            project_id=command.project_id,
        )
        await self._event_publisher.publish([event])
