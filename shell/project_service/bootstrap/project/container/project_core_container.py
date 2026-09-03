from __future__ import annotations

from dependency_injector import containers, providers

from shell.platform.application.bus.command_bus import CommandBus
from shell.platform.application.bus.event_bus import EventBus
from shell.platform.application.bus.event_bus_publisher import EventBusPublisher
from shell.platform.application.bus.query_bus import QueryBus
from shell.platform.infrastructure.identity.uuid_id_generator import UuidIdGenerator
from shell.platform.infrastructure.mapping.reflective_integration_mapper import (
    ReflectiveIntegrationMapper,
)
from shell.platform.infrastructure.messaging.command.processor.command_inbox_processor import (
    CommandInboxProcessor,
)
from shell.platform.infrastructure.messaging.command_transport import (
    CommandOutboxToTransportRelay,
)
from shell.platform.infrastructure.messaging.command_transport.rabbit import (
    RabbitCommandDeliveryTransport,
    RabbitCommandInboxConsumer,
)
from shell.platform.infrastructure.messaging.event.processor.event_inbox_processor import (
    EventInboxProcessor,
)
from shell.platform.infrastructure.messaging.event_transport import EventOutboxToTransportRelay
from shell.platform.infrastructure.messaging.event_transport.rabbit import (
    RabbitEventDeliveryTransport,
    RabbitEventInboxConsumer,
)
from shell.platform.infrastructure.messaging.inbox.envelope_validator import (
    envelope_policy_from_catalog,
)
from shell.platform.infrastructure.messaging.inbox.inbox_metrics_service import (
    InboxMetricsService,
)
from shell.platform.infrastructure.messaging.outbox.outbox_metrics_service import (
    OutboxMetricsService,
)
from shell.platform.infrastructure.persistence.sql import build_session_factory
from shell.platform.infrastructure.process.saga import build_command_delivery_dispatcher
from shell.platform.infrastructure.process.saga.repositories.sql_saga_repository import (
    SqlSagaRepository,
)
from shell.platform.infrastructure.process.saga.repositories.sql_saga_timeout_repository import (
    SqlSagaTimeoutRepository,
)
from shell.platform.infrastructure.process.saga.worker.saga_timeout_processor import (
    SagaTimeoutProcessor,
)
from shell.platform.infrastructure.serialization.upcaster import PayloadUpcaster
from shell.platform.infrastructure.time.system_clock import SystemClock
from shell.platform.observability.infrastructure.health.composite_readiness_probe import (
    CompositeReadinessProbe,
)
from shell.platform.observability.infrastructure.health.rabbit_readiness_probe import (
    RabbitReadinessProbe,
)
from shell.platform.observability.infrastructure.health.sql_readiness_probe import SqlReadinessProbe
from shell.platform.observability.infrastructure.metrics.prometheus_metrics_backend import (
    PrometheusMetricsBackend,
)
from shell.platform.observability.infrastructure.metrics.registry import MetricsRegistry
from shell.platform.process.saga.saga_timed_out import SagaTimedOut
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
from shell.project_service.application.project.project_provision.command_handlers.provision_workspace_handler import (
    ProvisionWorkspaceHandler,
)
from shell.project_service.application.project.project_provision.command_handlers.release_workspace_handler import (
    ReleaseWorkspaceHandler,
)
from shell.project_service.application.project.project_provision.commands.provision_workspace_command import (
    ProvisionWorkspaceCommand,
)
from shell.project_service.application.project.project_provision.commands.release_workspace_command import (
    ReleaseWorkspaceCommand,
)
from shell.project_service.application.project.project_provision.commands.start_project_provision_command import (
    StartProjectProvisionCommand,
)
from shell.project_service.application.project.project_provision.integration_events.workspace_provision_failed_integration_event import (
    WorkspaceProvisionFailedIntegrationEvent,
)
from shell.project_service.application.project.project_provision.integration_events.workspace_provisioned_integration_event import (
    WorkspaceProvisionedIntegrationEvent,
)
from shell.project_service.application.project.project_provision.integration_events.workspace_released_integration_event import (
    WorkspaceReleasedIntegrationEvent,
)
from shell.project_service.application.project.project_skill.queries.get_project_skill_by_id_query import (
    GetProjectSkillByIdQuery,
)
from shell.project_service.application.project.project_skill.query_handlers.get_project_skill_by_id_handler import (
    GetProjectSkillByIdHandler,
)
from shell.project_service.bootstrap.project.command_contracts import (
    PROJECT_COMMAND_CONTRACTS,
    build_project_command_registry,
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
from shell.project_service.process.project.project_provision.handlers.saga_timeout_handler import (
    ProjectProvisionTimeoutHandler,
)
from shell.project_service.process.project.project_provision.handlers.start_project_provision_handler import (
    StartProjectProvisionHandler,
)
from shell.project_service.process.project.project_provision.handlers.workspace_provision_failed_handler import (
    WorkspaceProvisionFailedSagaHandler,
)
from shell.project_service.process.project.project_provision.handlers.workspace_provisioned_handler import (
    WorkspaceProvisionedSagaHandler,
)
from shell.project_service.process.project.project_provision.handlers.workspace_released_handler import (
    WorkspaceReleasedSagaHandler,
)
from shell.project_service.process.project.project_provision.manager import (
    build_project_provision_manager_factory,
)


class ProjectCoreContainer(containers.DeclarativeContainer):
    config = providers.Configuration()
    session_factory = providers.Singleton(build_session_factory, url=config.db_url)
    command_bus = providers.Singleton(CommandBus)
    persistence_delivery_models = providers.Object(PERSISTENCE_DELIVERY_MODELS)
    event_bus = providers.Singleton(EventBus)
    event_publisher = providers.Singleton(EventBusPublisher, event_bus=event_bus)
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
    event_delivery_transport = providers.Factory(
        RabbitEventDeliveryTransport, url=config.broker_url
    )
    outbox_to_transport_relay_factory = providers.Factory(
        EventOutboxToTransportRelay,
        session_factory=session_factory,
        models=persistence_delivery_models.provided.events,
        transport=event_delivery_transport,
    )
    command_delivery_transport = providers.Factory(
        RabbitCommandDeliveryTransport, url=config.broker_url
    )
    command_outbox_to_transport_relay_factory = providers.Factory(
        CommandOutboxToTransportRelay,
        session_factory=session_factory,
        models=persistence_delivery_models.provided.commands,
        transport=command_delivery_transport,
    )
    saga_timeout_processor_factory = providers.Factory(
        SagaTimeoutProcessor,
        session_factory=session_factory,
        event_bus=event_bus,
        models=persistence_delivery_models.provided.sagas,
        heartbeat_interval_seconds=config.worker_heartbeat_interval_seconds,
        max_batch_time_seconds=config.worker_max_batch_time_seconds,
    )
    command_delivery_dispatcher = providers.Singleton(
        build_command_delivery_dispatcher,
        commands=providers.Object(PROJECT_COMMAND_CONTRACTS),
        models=persistence_delivery_models.provided.commands,
        source_service="project",
    )
    saga_repository = providers.Singleton(
        SqlSagaRepository,
        session_factory=session_factory,
        models=persistence_delivery_models.provided.sagas,
    )
    saga_timeout_repository = providers.Singleton(
        SqlSagaTimeoutRepository,
        session_factory=session_factory,
        models=persistence_delivery_models.provided.sagas,
        source_service="project",
    )
    project_provision_manager_factory = providers.Singleton(
        build_project_provision_manager_factory,
        repository=saga_repository,
        dispatcher=command_delivery_dispatcher,
        timeouts=saga_timeout_repository,
    )
    start_project_provision_handler_factory = providers.Factory(
        StartProjectProvisionHandler,
        manager_factory=project_provision_manager_factory,
        repository=saga_repository,
    )
    provision_workspace_handler_factory = providers.Factory(
        ProvisionWorkspaceHandler,
        event_publisher=event_publisher,
    )
    release_workspace_handler_factory = providers.Factory(
        ReleaseWorkspaceHandler,
        event_publisher=event_publisher,
    )
    workspace_provisioned_saga_handler_factory = providers.Factory(
        WorkspaceProvisionedSagaHandler,
        manager_factory=project_provision_manager_factory,
        repository=saga_repository,
    )
    workspace_provision_failed_saga_handler_factory = providers.Factory(
        WorkspaceProvisionFailedSagaHandler,
        manager_factory=project_provision_manager_factory,
        repository=saga_repository,
    )
    workspace_released_saga_handler_factory = providers.Factory(
        WorkspaceReleasedSagaHandler,
        manager_factory=project_provision_manager_factory,
        repository=saga_repository,
    )
    project_provision_timeout_handler_factory = providers.Factory(
        ProjectProvisionTimeoutHandler,
        manager_factory=project_provision_manager_factory,
        repository=saga_repository,
    )
    command_registry = providers.Object(build_project_command_registry())
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
        RabbitCommandInboxConsumer,
        url=config.broker_url,
        session_factory=session_factory,
        models=persistence_delivery_models.provided.commands,
        service_name="project",
    )
    rabbit_inbox_consumer_factory = providers.Factory(
        RabbitEventInboxConsumer,
        url=config.broker_url,
        session_factory=session_factory,
        models=persistence_delivery_models.provided.events,
        queue_name="shell-project-event-inbox",
    )
    metrics_exporter = providers.Singleton(MetricsRegistry)
    metrics_backend = providers.Singleton(PrometheusMetricsBackend, registry=metrics_exporter)
    inbox_metrics_service = providers.Singleton(
        InboxMetricsService,
        session_factory=session_factory,
        inbox_model=persistence_delivery_models.provided.events.inbox,
        backend=metrics_backend,
    )
    outbox_metrics_service = providers.Singleton(
        OutboxMetricsService,
        session_factory=session_factory,
        outbox_model=persistence_delivery_models.provided.events.outbox,
        backend=metrics_backend,
    )
    readiness_probe = providers.Singleton(
        CompositeReadinessProbe,
        probes=providers.List(
            providers.Singleton(
                SqlReadinessProbe,
                session_factory=session_factory,
                inbox_model=persistence_delivery_models.provided.events.inbox,
                max_backlog=1000,
                worker_heartbeat_model=persistence_delivery_models.provided.worker_heartbeat,
            ),
            providers.Singleton(
                RabbitReadinessProbe,
                url_provider=providers.Object(config.broker_url),
            ),
        ),
    )
    integration_mapper = providers.Singleton(ReflectiveIntegrationMapper)
    unit_of_work_factory = providers.Factory(
        SqlAlchemyProjectUnitOfWork,
        session_factory=session_factory,
        mapper=integration_mapper,
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
    container.command_bus().register(
        StartProjectProvisionCommand, container.start_project_provision_handler_factory
    )
    container.command_bus().register(
        ProvisionWorkspaceCommand, container.provision_workspace_handler_factory
    )
    container.command_bus().register(
        ReleaseWorkspaceCommand, container.release_workspace_handler_factory
    )
    container.event_bus().subscribe(
        WorkspaceProvisionedIntegrationEvent,
        container.workspace_provisioned_saga_handler_factory,
    )
    container.event_bus().subscribe(
        WorkspaceProvisionFailedIntegrationEvent,
        container.workspace_provision_failed_saga_handler_factory,
    )
    container.event_bus().subscribe(
        WorkspaceReleasedIntegrationEvent,
        container.workspace_released_saga_handler_factory,
    )
    container.event_bus().subscribe(
        SagaTimedOut,
        container.project_provision_timeout_handler_factory,
    )
    container.query_bus().register(GetProjectByIdQuery, container.get_project_by_id_handler_factory)
    container.query_bus().register(ListProjectsQuery, container.list_projects_handler_factory)
    container.query_bus().register(
        GetProjectSkillByIdQuery, container.get_project_skill_by_id_handler_factory
    )
