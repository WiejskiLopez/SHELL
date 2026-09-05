"""Saga handler — reakcja na timeout kroku provisionowania."""

from __future__ import annotations

from typing import TYPE_CHECKING

from saga_orchestration.process.saga.saga_timed_out import SagaTimedOut

from shell.platform.application.event_handlers.event_handler import EventHandler
from shell.project_service.process.project.project_provision.manager import SAGA_TYPE

if TYPE_CHECKING:
    from collections.abc import Callable

    from saga_orchestration.process.saga.ports.saga_repository import SagaRepository

    from shell.project_service.process.project.project_provision.manager import (
        ProjectProvisionSagaManager,
    )


class ProjectProvisionTimeoutHandler(EventHandler[SagaTimedOut]):
    def __init__(
        self,
        manager_factory: Callable[..., ProjectProvisionSagaManager],
        repository: SagaRepository,
    ) -> None:
        self._manager_factory = manager_factory
        self._repository = repository

    async def handle(self, event: SagaTimedOut) -> None:
        if event.saga_key == "":
            return
        instance = await self._repository.get_by_key(SAGA_TYPE, event.saga_key)
        if instance is None or instance.saga_id != event.saga_id:
            return
        manager = self._manager_factory(event.saga_key, saga_id=event.saga_id)
        await manager.on_timeout(event)