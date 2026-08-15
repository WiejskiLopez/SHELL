from __future__ import annotations

from dependency_injector import containers, providers

from shell.platform.application.bus.command_bus import CommandBus
from shell.platform.application.bus.event_bus import EventBus
from shell.platform.application.bus.query_bus import QueryBus
from shell.platform.infrastructure.health.sql_readiness_probe import SqlReadinessProbe
from shell.platform.infrastructure.identity.uuid_id_generator import UuidIdGenerator
from shell.platform.infrastructure.messaging.command.processor.command_inbox_processor import (
    CommandInboxProcessor,
)
from shell.platform.infrastructure.messaging.event.processor.event_inbox_processor import (
    EventInboxProcessor,
)
from shell.platform.infrastructure.messaging.inbox.envelope_validator import (
    envelope_policy_from_catalog,
)
from shell.platform.infrastructure.messaging.inbox.inbox_metrics_service import (
    InboxMetricsService,
)
from shell.platform.infrastructure.messaging.transport.rabbit import RabbitInboxConsumer
from shell.platform.infrastructure.metrics.logging_metrics_backend import (
    LoggingMetricsBackend,
)
from shell.platform.infrastructure.persistence.sql import build_session_factory
from shell.platform.infrastructure.serialization.command_registry import (
    build_command_registry,
    discover_command_types,
)
from shell.platform.infrastructure.serialization.upcaster import PayloadUpcaster
from shell.platform.infrastructure.time.system_clock import SystemClock
from shell.project_service.application.project.project.command_handlers.change_project_handler import (
    ChangeProjectHandler,
)
from shell.project_service.application.project.project.command_handlers.create_project_handler import (
    CreateProjectHandler,
)
from shell.project_service.application.project.project.command_handlers.delete_project_handler import (
    DeleteProjectHandler,
)
from shell.project_service.application.project.project.commands.change_project_command import (
    ChangeProjectCommand,
)
from shell.project_service.application.project.project.commands.create_project_command import (
    CreateProjectCommand,
)
from shell.project_service.application.project.project.commands.delete_project_command import (
    DeleteProjectCommand,
)
from shell.project_service.application.project.project.queries.get_project_by_id_query import (
    GetProjectByIdQuery,
)
from shell.project_service.application.project.project.queries.list_projects_query import (
    ListProjectsQuery,
)
from shell.project_service.application.project.project.query_handlers.get_project_by_id_handler import (
    GetProjectByIdHandler,
)
from shell.project_service.application.project.project.query_handlers.list_projects_handler import (
    ListProjectsHandler,
)
from shell.project_service.application.project.project_skill.queries.get_project_skill_by_id_query import (
    GetProjectSkillByIdQuery,
)
from shell.project_service.application.project.project_skill.query_handlers.get_project_skill_by_id_handler import (
    GetProjectSkillByIdHandler,
)
from shell.project_service.bootstrap.project.contract_catalog import PROJECT_CONTRACT_CATALOG
from shell.project_service.bootstrap.project.event_registry import build_project_event_registry
from shell.project_service.infrastructure.project.persistence.sql.models.base import (
    PERSISTENCE_DELIVERY_MODELS,
)
from shell.project_service.infrastructure.project.project.persistence.sql.services.project_query_service import (
    ProjectQueryService,
)
from shell.project_service.infrastructure.project.project.persistence.sql.unit_of_work import (
    SqlAlchemyProjectUnitOfWork,
)
from shell.project_service.infrastructure.project.project_skill.persistence.sql.services.project_skill_query_service import (
    ProjectSkillQueryService,
)


class ProjectCoreContainer(containers.DeclarativeContainer):
    config = providers.Configuration()
    session_factory = providers.Singleton(build_session_factory, url=config.db_url)
    command_bus = providers.Singleton(CommandBus)
    persistence_delivery_models = providers.Object(PERSISTENCE_DELIVERY_MODELS)
    event_bus = providers.Singleton(EventBus)
    event_registry = providers.Singleton(build_project_event_registry)
    event_inbox_processor_factory = providers.Factory(
        EventInboxProcessor,
        session_factory=session_factory,
        event_bus=event_bus,
        models=persistence_delivery_models.provided.events,
        registry=event_registry,
        processed_delivery_model=persistence_delivery_models.provided.processed_delivery,
        consumer_name="project",
        worker_id=config.worker_id,
        heartbeat_interval_seconds=config.worker_heartbeat_interval_seconds,
        max_batch_time_seconds=config.worker_max_batch_time_seconds,
        envelope_policy=envelope_policy_from_catalog(PROJECT_CONTRACT_CATALOG),
        upcaster=providers.Singleton(PayloadUpcaster),
    )
    command_registry = providers.Object(
        build_command_registry(discover_command_types("shell.project_service.application.project"))
    )
    command_inbox_processor_factory = providers.Factory(
        CommandInboxProcessor,
        session_factory=session_factory,
        command_bus=command_bus,
        models=persistence_delivery_models.provided.commands,
        registry=command_registry,
        processed_delivery_model=persistence_delivery_models.provided.processed_delivery,
        consumer_name="project-command",
        worker_id=config.command_worker_id,
        heartbeat_interval_seconds=config.worker_heartbeat_interval_seconds,
        max_batch_time_seconds=config.worker_max_batch_time_seconds,
        upcaster=providers.Singleton(PayloadUpcaster),
    )
    rabbit_command_inbox_consumer_factory = providers.Factory(
        RabbitInboxConsumer,
        url=config.broker_url,
        session_factory=session_factory,
        models=persistence_delivery_models.provided.commands,
        queue_name="shell-project-command-inbox",
        routing_keys=["command.#"],
    )
    rabbit_inbox_consumer_factory = providers.Factory(
        RabbitInboxConsumer,
        url=config.broker_url,
        session_factory=session_factory,
        models=persistence_delivery_models.provided.events,
        queue_name="shell-project-event-inbox",
    )
    inbox_metrics_service = providers.Singleton(
        InboxMetricsService,
        session_factory=session_factory,
        inbox_model=persistence_delivery_models.provided.events.inbox,
        backend=LoggingMetricsBackend(),
    )
    readiness_probe = providers.Singleton(
        SqlReadinessProbe,
        session_factory=session_factory,
        inbox_model=persistence_delivery_models.provided.events.inbox,
        max_backlog=1000,
        worker_heartbeat_model=persistence_delivery_models.provided.worker_heartbeat,
    )
    unit_of_work_factory = providers.Factory(
        SqlAlchemyProjectUnitOfWork,
        session_factory=session_factory,
        models=persistence_delivery_models,
    )
    clock_factory = providers.Factory(SystemClock)
    id_generator_factory = providers.Factory(UuidIdGenerator)
    query_bus = providers.Singleton(QueryBus)
    project_query_service = providers.Singleton(
        ProjectQueryService, session_factory=session_factory
    )
    project_skill_query_service = providers.Singleton(
        ProjectSkillQueryService, session_factory=session_factory
    )
    get_project_skill_by_id_handler_factory = providers.Factory(
        GetProjectSkillByIdHandler, queries=project_skill_query_service
    )
    create_project_handler_factory = providers.Factory(
        CreateProjectHandler,
        unit_of_work=unit_of_work_factory,
        clock=clock_factory,
        id_generator=id_generator_factory,
    )
    change_project_handler_factory = providers.Factory(
        ChangeProjectHandler, unit_of_work=unit_of_work_factory, clock=clock_factory
    )
    delete_project_handler_factory = providers.Factory(
        DeleteProjectHandler, unit_of_work=unit_of_work_factory, clock=clock_factory
    )
    get_project_by_id_handler_factory = providers.Factory(
        GetProjectByIdHandler, queries=project_query_service
    )
    list_projects_handler_factory = providers.Factory(
        ListProjectsHandler, queries=project_query_service
    )


def configure_project_container(container: ProjectCoreContainer) -> None:
    container.command_bus().register(CreateProjectCommand, container.create_project_handler_factory)
    container.command_bus().register(ChangeProjectCommand, container.change_project_handler_factory)
    container.command_bus().register(DeleteProjectCommand, container.delete_project_handler_factory)
    container.query_bus().register(GetProjectByIdQuery, container.get_project_by_id_handler_factory)
    container.query_bus().register(ListProjectsQuery, container.list_projects_handler_factory)
    container.query_bus().register(
        GetProjectSkillByIdQuery, container.get_project_skill_by_id_handler_factory
    )
