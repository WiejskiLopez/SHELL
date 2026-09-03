from __future__ import annotations

from typing import TYPE_CHECKING

from shell.platform.application.command_handlers.command_handler import CommandHandler
from shell.platform.domain.value_objects.changed_at import ChangedAt
from shell.project_service.application.project.project.commands.change_project_command import (
    ChangeProjectCommand,
)
from shell.project_service.application.project.project.exceptions.project_not_found_error import (
    ProjectNotFoundError,
)
from shell.project_service.domain.project.aggregates.project.repositories.project_repository import (
    ProjectRepository,
)
from shell.project_service.domain.project.aggregates.project.value_objects.project_id import (
    ProjectId,
)
from shell.project_service.domain.project.aggregates.project.value_objects.project_name import (
    ProjectName,
)
from shell.project_service.domain.project.aggregates.project.value_objects.repo_url import RepoUrl

if TYPE_CHECKING:
    from shell.platform.application.ports.persistence.unit_of_work import UnitOfWork
    from shell.platform.domain.ports.time import Clock


class ChangeProjectHandler(CommandHandler[ChangeProjectCommand]):
    def __init__(self, unit_of_work: UnitOfWork, clock: Clock) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    async def handle(self, command: ChangeProjectCommand) -> None:
        async with self._unit_of_work as unit_of_work:
            project = await unit_of_work.repository(ProjectRepository).get_by_id(
                ProjectId(command.project_id)
            )
            if project is None:
                raise ProjectNotFoundError(command.project_id)
            now = ChangedAt.from_datetime(self._clock.now())
            project.change(
                name=ProjectName(command.name) if command.name is not None else None,
                repo_url=RepoUrl(command.repo_url) if command.repo_url is not None else None,
                now=now,
            )
            await unit_of_work.save(ProjectRepository, project)
