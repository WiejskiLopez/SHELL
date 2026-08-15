from __future__ import annotations

from typing import TYPE_CHECKING

from shell.platform.domain.value_objects.deleted_at import DeletedAt
from shell.project_service.domain.project.aggregates.project.repositories.project_repository import (
    ProjectRepository,
)
from shell.project_service.domain.project.aggregates.project.value_objects.project_id import (
    ProjectId,
)

if TYPE_CHECKING:
    from shell.platform.application.ports.unit_of_work import UnitOfWork
    from shell.platform.domain.ports.time import Clock
    from shell.project_service.application.project.project.commands.delete_project_command import (
        DeleteProjectCommand,
    )


class ProjectNotFoundError(Exception):
    pass


class ProjectAlreadyDeletedError(Exception):
    pass


class DeleteProjectHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    async def handle(self, command: DeleteProjectCommand) -> None:
        project_id = ProjectId(command.project_id)

        async with self._unit_of_work as unit_of_work:
            project = await unit_of_work.repository(ProjectRepository).get_by_id(project_id)
            if project is None:
                raise ProjectNotFoundError(f"Project '{command.project_id}' not found")

            now = DeletedAt.from_datetime(self._clock.now())
            project.delete(now)
            await unit_of_work.save(ProjectRepository, project)
