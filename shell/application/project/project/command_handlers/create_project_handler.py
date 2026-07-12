from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.project.aggregates.project.project import Project
from shell.domain.project.aggregates.project.repositories.project_repository import (
    ProjectRepository,
)
from shell.domain.project.aggregates.project.value_objects.project_id import ProjectId
from shell.domain.project.aggregates.project.value_objects.project_name import ProjectName
from shell.domain.project.aggregates.project.value_objects.repo_url import RepoUrl
from shell.platform.domain.value_objects.created_at import CreatedAt

if TYPE_CHECKING:
    from shell.application.project.project.commands.create_project_command import (
        CreateProjectCommand,
    )
    from shell.platform.application.ports.ports import Clock, IdGenerator, UnitOfWork


class CreateProjectHandler:
    def __init__(self, unit_of_work: UnitOfWork, clock: Clock, id_generator: IdGenerator) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._id_generator = id_generator

    async def handle(self, command: CreateProjectCommand) -> ProjectId:
        project_id = self._id_generator.new_id(ProjectId)
        now = self._clock.now()
        project = Project(
            id=project_id,
            name=ProjectName(command.name),
            repo_url=RepoUrl(command.repo_url) if command.repo_url else RepoUrl(None),
            created_at=CreatedAt.from_datetime(now),
        )
        async with self._unit_of_work as unit_of_work:
            await unit_of_work.save(ProjectRepository, project)
        return project_id
