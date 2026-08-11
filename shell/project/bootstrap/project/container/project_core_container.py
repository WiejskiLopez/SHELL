from __future__ import annotations

from dependency_injector import containers, providers

from shell.platform.application.bus.command_bus import CommandBus
from shell.platform.application.bus.query_bus import QueryBus
from shell.platform.infrastructure.identity.uuid_id_generator import UuidIdGenerator
from shell.platform.infrastructure.persistence.sql import build_session_factory
from shell.platform.infrastructure.time.system_clock import SystemClock
from shell.project.application.project.project.command_handlers.create_project_handler import (
    CreateProjectHandler,
)
from shell.project.application.project.project.command_handlers.delete_project_handler import (
    DeleteProjectHandler,
)
from shell.project.application.project.project.command_handlers.update_project_handler import (
    UpdateProjectHandler,
)
from shell.project.application.project.project.commands.create_project_command import (
    CreateProjectCommand,
)
from shell.project.application.project.project.commands.delete_project_command import (
    DeleteProjectCommand,
)
from shell.project.application.project.project.commands.update_project_command import (
    UpdateProjectCommand,
)
from shell.project.application.project.project.queries.get_project_by_id_query import (
    GetProjectByIdQuery,
)
from shell.project.application.project.project.queries.list_projects_query import ListProjectsQuery
from shell.project.application.project.project.query_handlers.get_project_by_id_handler import (
    GetProjectByIdHandler,
)
from shell.project.application.project.project.query_handlers.list_projects_handler import (
    ListProjectsHandler,
)
from shell.project.infrastructure.project.project.persistence.sql.services.project_query_service import (
    ProjectQueryService,
)
from shell.project.infrastructure.project.project.persistence.sql.unit_of_work import (
    SqlAlchemyProjectUnitOfWork,
)


class ProjectCoreContainer(containers.DeclarativeContainer):
    config = providers.Configuration()
    session_factory = providers.Singleton(build_session_factory, url=config.db_url)
    unit_of_work_factory = providers.Factory(SqlAlchemyProjectUnitOfWork, session_factory=session_factory)
    clock_factory = providers.Factory(SystemClock)
    id_generator_factory = providers.Factory(UuidIdGenerator)
    command_bus = providers.Singleton(CommandBus)
    query_bus = providers.Singleton(QueryBus)
    project_query_service = providers.Singleton(ProjectQueryService, session_factory=session_factory)
    create_project_handler_factory = providers.Factory(CreateProjectHandler, unit_of_work=unit_of_work_factory, clock=clock_factory, id_generator=id_generator_factory)
    update_project_handler_factory = providers.Factory(UpdateProjectHandler, unit_of_work=unit_of_work_factory, clock=clock_factory)
    delete_project_handler_factory = providers.Factory(DeleteProjectHandler, unit_of_work=unit_of_work_factory, clock=clock_factory)
    get_project_by_id_handler_factory = providers.Factory(GetProjectByIdHandler, queries=project_query_service)
    list_projects_handler_factory = providers.Factory(ListProjectsHandler, queries=project_query_service)


def configure_project_container(container: ProjectCoreContainer) -> None:
    container.command_bus().register(CreateProjectCommand, container.create_project_handler_factory)
    container.command_bus().register(UpdateProjectCommand, container.update_project_handler_factory)
    container.command_bus().register(DeleteProjectCommand, container.delete_project_handler_factory)
    container.query_bus().register(GetProjectByIdQuery, container.get_project_by_id_handler_factory)
    container.query_bus().register(ListProjectsQuery, container.list_projects_handler_factory)
