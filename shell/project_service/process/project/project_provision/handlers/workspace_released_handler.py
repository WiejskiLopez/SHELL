"""Saga handler — reakcja na zakończenie kompensacji workspace'u."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.platform.application.event_handlers.event_handler import EventHandler
from shell.project_service.application.project.project_provision.integration_events.workspace_released_integration_event import (
    WorkspaceReleasedIntegrationEvent,
)
from shell.project_service.process.project.project_provision.manager import SAGA_TYPE

if TYPE_CHECKING:
    from collections.abc import Callable

    from shell.platform.process.saga.ports.saga_repository import SagaRepository
    from shell.project_service.process.project.project_provision.manager import (
        ProjectProvisionSagaManager,
    )


class WorkspaceReleasedSagaHandler(EventHandler[WorkspaceReleasedIntegrationEvent]):
    def __init__(
        self,
        manager_factory: Callable[..., ProjectProvisionSagaManager],
        repository: SagaRepository,
    ) -> None:
        self._manager_factory = manager_factory
        self._repository = repository

    async def handle(self, event: WorkspaceReleasedIntegrationEvent) -> None:
        instance = await self._repository.get_by_key(SAGA_TYPE, event.project_id)
        if instance is None:
            return
        manager = self._manager_factory(event.project_id, saga_id=instance.saga_id)
        await manager.on_event(event)