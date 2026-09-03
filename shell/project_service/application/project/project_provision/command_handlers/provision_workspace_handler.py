from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from shell.platform.application.command_handlers.command_handler import CommandHandler
from shell.platform.application.context.causation_id import get_causation_id
from shell.platform.application.context.correlation_id import get_or_create_correlation_id
from shell.project_service.application.project.project_provision.commands.provision_workspace_command import (
    ProvisionWorkspaceCommand,
)
from shell.project_service.application.project.project_provision.integration_events.workspace_provision_failed_integration_event import (
    WorkspaceProvisionFailedIntegrationEvent,
)
from shell.project_service.application.project.project_provision.integration_events.workspace_provisioned_integration_event import (
    WorkspaceProvisionedIntegrationEvent,
)

if TYPE_CHECKING:
    from shell.platform.application.ports.messaging.event_publisher import EventPublisher


def _now() -> datetime:
    return datetime.now(tz=UTC)


class ProvisionWorkspaceHandler(CommandHandler[ProvisionWorkspaceCommand]):
    """Uczestnik kroku — w pilocie stubsuje efekt zewnętrznego serwisu.

    Publikuje fakt rezultatu (sukces albo porażka). W produkcji efekt realizuje
    właściwy agregat uczestnika, a fakt wychodzi przez outbox_event.
    """

    def __init__(self, event_publisher: EventPublisher) -> None:
        self._event_publisher = event_publisher

    async def handle(self, command: ProvisionWorkspaceCommand) -> None:
        now = _now()
        if command.fail:
            await self._event_publisher.publish(
                [
                    WorkspaceProvisionFailedIntegrationEvent(
                        event_id=str(uuid.uuid4()),
                        correlation_id=get_or_create_correlation_id(),
                        causation_id=get_causation_id(),
                        occurred_at=now,
                        aggregate_id=command.project_id,
                        schema_version=1,
                        project_id=command.project_id,
                        reason="workspace_unavailable",
                    )
                ]
            )
            return
        await self._event_publisher.publish(
            [
                WorkspaceProvisionedIntegrationEvent(
                    event_id=str(uuid.uuid4()),
                    correlation_id=get_or_create_correlation_id(),
                    causation_id=get_causation_id(),
                    occurred_at=now,
                    aggregate_id=command.project_id,
                    schema_version=1,
                    project_id=command.project_id,
                )
            ]
        )
