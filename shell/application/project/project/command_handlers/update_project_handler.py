from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.project.aggregates.project.repositories.project_repository import (
    ProjectRepository,
)
from shell.domain.project.aggregates.project.value_objects.project_id import ProjectId
from shell.domain.project.aggregates.project.value_objects.project_name import ProjectName
from shell.domain.project.aggregates.project.value_objects.repo_url import RepoUrl
from shell.platform.domain.exceptions import DomainError

if TYPE_CHECKING:
    from shell.application.project.project.commands.update_project_command import (
        UpdateProjectCommand,
    )
    from shell.platform.application.ports.ports import Clock, UnitOfWork


class ProjectNotFoundError(DomainError):
    def __init__(self, project_id: str) -> None:
        super().__init__(f"Project not found: {project_id}", code="project_not_found")


class UpdateProjectHandler:
    def __init__(self, unit_of_work: UnitOfWork, clock: Clock) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    async def handle(self, command: UpdateProjectCommand) -> None:
        async with self._unit_of_work as unit_of_work:
            project = await unit_of_work.repository(ProjectRepository).get_by_id(
                ProjectId(command.project_id)
            )
            if project is None:
                raise ProjectNotFoundError(command.project_id)
            now = self._clock.now()
            project.update(
                name=ProjectName(command.name) if command.name else project.name,
                repo_url=RepoUrl(command.repo_url) if command.repo_url is not None else project.repo_url,
                now=now,
            )
            await unit_of_work.save(ProjectRepository, project)
