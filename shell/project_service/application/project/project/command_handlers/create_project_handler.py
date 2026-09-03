from __future__ import annotations

from typing import TYPE_CHECKING

from shell.platform.application.command_handlers.command_handler import CommandHandler
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.project_service.application.project.project.commands.create_project_command import (
    CreateProjectCommand,
)
from shell.project_service.domain.project.aggregates.project.project import Project
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
    from shell.platform.domain.ports.identity import IdGenerator
    from shell.platform.domain.ports.time import Clock


class CreateProjectHandler(CommandHandler[CreateProjectCommand]):
    def __init__(self, unit_of_work: UnitOfWork, clock: Clock, id_generator: IdGenerator) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._id_generator = id_generator

    async def handle(self, command: CreateProjectCommand) -> ProjectId:
        project_id = self._id_generator.new_id(ProjectId)
        now = CreatedAt.from_datetime(self._clock.now())
        repo_url = RepoUrl(command.repo_url)
        project = Project.create(
            id_=project_id,
            name=ProjectName(command.name),
            repo_url=repo_url,
            now=now,
        )
        async with self._unit_of_work as unit_of_work:
            await unit_of_work.save(ProjectRepository, project)
        return project_id
