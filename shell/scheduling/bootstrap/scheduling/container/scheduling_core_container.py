from __future__ import annotations

from dependency_injector import containers, providers

from shell.platform.application.bus.command_bus import CommandBus
from shell.platform.application.bus.query_bus import QueryBus
from shell.platform.infrastructure.identity.uuid_id_generator import UuidIdGenerator
from shell.platform.infrastructure.persistence.sql import build_session_factory
from shell.platform.infrastructure.time.system_clock import SystemClock
from shell.scheduling.application.scheduling.scheduler_definition.command_handlers.create_scheduler_definition_handler import (
    CreateSchedulerDefinitionHandler,
)
from shell.scheduling.application.scheduling.scheduler_definition.command_handlers.delete_scheduler_definition_handler import (
    DeleteSchedulerDefinitionHandler,
)
from shell.scheduling.application.scheduling.scheduler_definition.command_handlers.update_scheduler_definition_handler import (
    UpdateSchedulerDefinitionHandler,
)
from shell.scheduling.application.scheduling.scheduler_definition.commands.create_scheduler_definition_command import (
    CreateSchedulerDefinitionCommand,
)
from shell.scheduling.application.scheduling.scheduler_definition.commands.delete_scheduler_definition_command import (
    DeleteSchedulerDefinitionCommand,
)
from shell.scheduling.application.scheduling.scheduler_definition.commands.update_scheduler_definition_command import (
    UpdateSchedulerDefinitionCommand,
)
from shell.scheduling.application.scheduling.scheduler_definition.queries.get_scheduler_definition_by_id_query import (
    GetSchedulerDefinitionByIdQuery,
)
from shell.scheduling.application.scheduling.scheduler_definition.query_handlers.get_scheduler_definition_by_id_handler import (
    GetSchedulerDefinitionByIdHandler,
)
from shell.scheduling.application.scheduling.scheduler_execution.command_handlers.create_scheduler_execution_handler import (
    CreateSchedulerExecutionHandler,
)
from shell.scheduling.application.scheduling.scheduler_execution.command_handlers.delete_scheduler_execution_handler import (
    DeleteSchedulerExecutionHandler,
)
from shell.scheduling.application.scheduling.scheduler_execution.command_handlers.update_scheduler_execution_handler import (
    UpdateSchedulerExecutionHandler,
)
from shell.scheduling.application.scheduling.scheduler_execution.commands.create_scheduler_execution_command import (
    CreateSchedulerExecutionCommand,
)
from shell.scheduling.application.scheduling.scheduler_execution.commands.delete_scheduler_execution_command import (
    DeleteSchedulerExecutionCommand,
)
from shell.scheduling.application.scheduling.scheduler_execution.commands.update_scheduler_execution_command import (
    UpdateSchedulerExecutionCommand,
)
from shell.scheduling.application.scheduling.scheduler_execution.queries.get_scheduler_execution_by_id_query import (
    GetSchedulerExecutionByIdQuery,
)
from shell.scheduling.application.scheduling.scheduler_execution.query_handlers.get_scheduler_execution_by_id_handler import (
    GetSchedulerExecutionByIdHandler,
)
from shell.scheduling.application.scheduling.scheduler_job.command_handlers.create_scheduler_job_handler import (
    CreateSchedulerJobHandler,
)
from shell.scheduling.application.scheduling.scheduler_job.command_handlers.delete_scheduler_job_handler import (
    DeleteSchedulerJobHandler,
)
from shell.scheduling.application.scheduling.scheduler_job.command_handlers.update_scheduler_job_handler import (
    UpdateSchedulerJobHandler,
)
from shell.scheduling.application.scheduling.scheduler_job.commands.create_scheduler_job_command import (
    CreateSchedulerJobCommand,
)
from shell.scheduling.application.scheduling.scheduler_job.commands.delete_scheduler_job_command import (
    DeleteSchedulerJobCommand,
)
from shell.scheduling.application.scheduling.scheduler_job.commands.update_scheduler_job_command import (
    UpdateSchedulerJobCommand,
)
from shell.scheduling.infrastructure.scheduling.scheduler_definition.persistence.sql.services.scheduler_definition_query_service import (
    SchedulerDefinitionQueryService,
)
from shell.scheduling.infrastructure.scheduling.scheduler_definition.persistence.sql.unit_of_work import (
    SqlAlchemySchedulerDefinitionUnitOfWork,
)
from shell.scheduling.infrastructure.scheduling.scheduler_execution.persistence.sql.services.scheduler_execution_query_service import (
    SchedulerExecutionQueryService,
)
from shell.scheduling.infrastructure.scheduling.scheduler_execution.persistence.sql.unit_of_work import (
    SqlAlchemySchedulerExecutionUnitOfWork,
)
from shell.scheduling.infrastructure.scheduling.scheduler_job.persistence.sql.services.scheduler_job_query_service import (
    SchedulerJobQueryService,
)


class SchedulingCoreContainer(containers.DeclarativeContainer):
    config = providers.Configuration()
    session_factory = providers.Singleton(build_session_factory, url=config.db_url)
    scheduler_definition_uow_factory = providers.Factory(SqlAlchemySchedulerDefinitionUnitOfWork, session_factory=session_factory)
    scheduler_execution_uow_factory = providers.Factory(SqlAlchemySchedulerExecutionUnitOfWork, session_factory=session_factory)
    clock_factory = providers.Factory(SystemClock)
    id_generator_factory = providers.Factory(UuidIdGenerator)
    command_bus = providers.Singleton(CommandBus)
    query_bus = providers.Singleton(QueryBus)
    scheduler_definition_query_service = providers.Singleton(SchedulerDefinitionQueryService, session_factory=session_factory)
    scheduler_execution_query_service = providers.Singleton(SchedulerExecutionQueryService, session_factory=session_factory)
    scheduler_job_query_service = providers.Singleton(SchedulerJobQueryService, session_factory=session_factory)
    create_scheduler_definition_handler_factory = providers.Factory(CreateSchedulerDefinitionHandler, unit_of_work=scheduler_definition_uow_factory, clock=clock_factory, id_generator=id_generator_factory)
    update_scheduler_definition_handler_factory = providers.Factory(UpdateSchedulerDefinitionHandler, unit_of_work=scheduler_definition_uow_factory, clock=clock_factory)
    delete_scheduler_definition_handler_factory = providers.Factory(DeleteSchedulerDefinitionHandler, unit_of_work=scheduler_definition_uow_factory, clock=clock_factory)
    create_scheduler_execution_handler_factory = providers.Factory(CreateSchedulerExecutionHandler, unit_of_work=scheduler_execution_uow_factory, clock=clock_factory, id_generator=id_generator_factory)
    update_scheduler_execution_handler_factory = providers.Factory(UpdateSchedulerExecutionHandler, unit_of_work=scheduler_execution_uow_factory, clock=clock_factory)
    delete_scheduler_execution_handler_factory = providers.Factory(DeleteSchedulerExecutionHandler, unit_of_work=scheduler_execution_uow_factory, clock=clock_factory)
    create_scheduler_job_handler_factory = providers.Factory(CreateSchedulerJobHandler, unit_of_work=scheduler_execution_uow_factory, clock=clock_factory, id_generator=id_generator_factory)
    update_scheduler_job_handler_factory = providers.Factory(UpdateSchedulerJobHandler, unit_of_work=scheduler_execution_uow_factory, clock=clock_factory)
    delete_scheduler_job_handler_factory = providers.Factory(DeleteSchedulerJobHandler, unit_of_work=scheduler_execution_uow_factory, clock=clock_factory)
    get_scheduler_definition_handler_factory = providers.Factory(GetSchedulerDefinitionByIdHandler, queries=scheduler_definition_query_service)
    get_scheduler_execution_handler_factory = providers.Factory(GetSchedulerExecutionByIdHandler, queries=scheduler_execution_query_service)


def configure_scheduling_container(container: SchedulingCoreContainer) -> None:
    command_bus = container.command_bus()
    query_bus = container.query_bus()
    for command, factory in ((CreateSchedulerDefinitionCommand, container.create_scheduler_definition_handler_factory), (UpdateSchedulerDefinitionCommand, container.update_scheduler_definition_handler_factory), (DeleteSchedulerDefinitionCommand, container.delete_scheduler_definition_handler_factory), (CreateSchedulerExecutionCommand, container.create_scheduler_execution_handler_factory), (UpdateSchedulerExecutionCommand, container.update_scheduler_execution_handler_factory), (DeleteSchedulerExecutionCommand, container.delete_scheduler_execution_handler_factory), (CreateSchedulerJobCommand, container.create_scheduler_job_handler_factory), (UpdateSchedulerJobCommand, container.update_scheduler_job_handler_factory), (DeleteSchedulerJobCommand, container.delete_scheduler_job_handler_factory)):
        command_bus.register(command, factory)
    query_bus.register(GetSchedulerDefinitionByIdQuery, container.get_scheduler_definition_handler_factory)
    query_bus.register(GetSchedulerExecutionByIdQuery, container.get_scheduler_execution_handler_factory)
