"""Start handler — inicjalizator sagi project_provision (rejestrowany na CommandBus)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.platform.application.command_handlers.command_handler import CommandHandler
from shell.project_service.application.project.project_provision.commands.start_project_provision_command import (
    StartProjectProvisionCommand,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from shell.platform.process.saga.ports.saga_repository import SagaRepository
    from shell.project_service.process.project.project_provision.manager import (
        ProjectProvisionSagaManager,
    )


class StartProjectProvisionHandler(CommandHandler[StartProjectProvisionCommand]):
    def __init__(
        self,
        manager_factory: Callable[..., ProjectProvisionSagaManager],
        repository: SagaRepository,
    ) -> None:
        self._manager_factory = manager_factory
        self._repository = repository

    async def handle(self, command: StartProjectProvisionCommand) -> None:
        instance = await self._repository.get_by_key("project_provision", command.project_id)
        if instance is not None:
            return
        manager = self._manager_factory(command.project_id)
        await manager.start(command.project_id, command.fail)
