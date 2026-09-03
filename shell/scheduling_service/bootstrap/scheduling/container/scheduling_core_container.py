from __future__ import annotations

from dependency_injector import containers, providers

from shell.platform.application.bus.command_bus import CommandBus
from shell.platform.application.bus.event_bus import EventBus
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
from shell.platform.infrastructure.serialization.registries.command_registry import (
    build_command_registry,
    discover_command_types,
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
from shell.scheduling_service.application.scheduling.scheduler_definition.command_handlers.change_scheduler_definition_handler import (
    ChangeSchedulerDefinitionHandler,
)
from shell.scheduling_service.application.scheduling.scheduler_definition.command_handlers.create_scheduler_definition_handler import (
    CreateSchedulerDefinitionHandler,
)
from shell.scheduling_service.application.scheduling.scheduler_definition.command_handlers.delete_scheduler_definition_handler import (
    DeleteSchedulerDefinitionHandler,
)
from shell.scheduling_service.application.scheduling.scheduler_definition.commands.change_scheduler_definition_command import (
    ChangeSchedulerDefinitionCommand,
)
from shell.scheduling_service.application.scheduling.scheduler_definition.commands.create_scheduler_definition_command import (
    CreateSchedulerDefinitionCommand,
)
from shell.scheduling_service.application.scheduling.scheduler_definition.commands.delete_scheduler_definition_command import (
    DeleteSchedulerDefinitionCommand,
)
from shell.scheduling_service.application.scheduling.scheduler_definition.queries.get_scheduler_definition_by_id_query import (
    GetSchedulerDefinitionByIdQuery,
)
from shell.scheduling_service.application.scheduling.scheduler_definition.query_handlers.get_scheduler_definition_by_id_handler import (
    GetSchedulerDefinitionByIdHandler,
)
from shell.scheduling_service.application.scheduling.scheduler_execution.command_handlers.change_scheduler_execution_handler import (
    ChangeSchedulerExecutionHandler,
)
from shell.scheduling_service.application.scheduling.scheduler_execution.command_handlers.create_scheduler_execution_handler import (
    CreateSchedulerExecutionHandler,
)
from shell.scheduling_service.application.scheduling.scheduler_execution.command_handlers.delete_scheduler_execution_handler import (
    DeleteSchedulerExecutionHandler,
)
from shell.scheduling_service.application.scheduling.scheduler_execution.commands.change_scheduler_execution_command import (
    ChangeSchedulerExecutionCommand,
)
from shell.scheduling_service.application.scheduling.scheduler_execution.commands.create_scheduler_execution_command import (
    CreateSchedulerExecutionCommand,
)
from shell.scheduling_service.application.scheduling.scheduler_execution.commands.delete_scheduler_execution_command import (
    DeleteSchedulerExecutionCommand,
)
from shell.scheduling_service.application.scheduling.scheduler_execution.queries.get_scheduler_execution_by_id_query import (
    GetSchedulerExecutionByIdQuery,
)
from shell.scheduling_service.application.scheduling.scheduler_execution.queries.list_scheduler_executions_query import (
    ListSchedulerExecutionsQuery,
)
from shell.scheduling_service.application.scheduling.scheduler_execution.query_handlers.get_scheduler_execution_by_id_handler import (
    GetSchedulerExecutionByIdHandler,
)
from shell.scheduling_service.application.scheduling.scheduler_execution.query_handlers.list_scheduler_executions_handler import (
    ListSchedulerExecutionsHandler,
)
from shell.scheduling_service.application.scheduling.scheduler_job.command_handlers.change_scheduler_job_handler import (
    ChangeSchedulerJobHandler,
)
from shell.scheduling_service.application.scheduling.scheduler_job.command_handlers.create_scheduler_job_handler import (
    CreateSchedulerJobHandler,
)
from shell.scheduling_service.application.scheduling.scheduler_job.command_handlers.delete_scheduler_job_handler import (
    DeleteSchedulerJobHandler,
)
from shell.scheduling_service.application.scheduling.scheduler_job.commands.change_scheduler_job_command import (
    ChangeSchedulerJobCommand,
)
from shell.scheduling_service.application.scheduling.scheduler_job.commands.create_scheduler_job_command import (
    CreateSchedulerJobCommand,
)
from shell.scheduling_service.application.scheduling.scheduler_job.commands.delete_scheduler_job_command import (
    DeleteSchedulerJobCommand,
)
from shell.scheduling_service.application.scheduling.scheduler_job.queries.get_scheduler_job_by_id_query import (
    GetSchedulerJobByIdQuery,
)
from shell.scheduling_service.application.scheduling.scheduler_job.queries.list_scheduler_jobs_query import (
    ListSchedulerJobsQuery,
)
from shell.scheduling_service.application.scheduling.scheduler_job.query_handlers.get_scheduler_job_by_id_handler import (
    GetSchedulerJobByIdHandler,
)
from shell.scheduling_service.application.scheduling.scheduler_job.query_handlers.list_scheduler_jobs_handler import (
    ListSchedulerJobsHandler,
)
from shell.scheduling_service.bootstrap.scheduling.contract_catalog import (
    SCHEDULING_CONTRACT_CATALOG,
)
from shell.scheduling_service.bootstrap.scheduling.event_registry import (
    build_scheduling_event_registry,
)
from shell.scheduling_service.infrastructure.scheduling.persistence.sql.models.base import (
    PERSISTENCE_DELIVERY_MODELS,
)
from shell.scheduling_service.infrastructure.scheduling.scheduler_definition.persistence.sql.services.scheduler_definition_query_service import (
    SchedulerDefinitionQueryService,
)
from shell.scheduling_service.infrastructure.scheduling.scheduler_definition.persistence.sql.unit_of_work import (
    SqlAlchemySchedulerDefinitionUnitOfWork,
)
from shell.scheduling_service.infrastructure.scheduling.scheduler_execution.persistence.sql.services.scheduler_execution_query_service import (
    SchedulerExecutionQueryService,
)
from shell.scheduling_service.infrastructure.scheduling.scheduler_execution.persistence.sql.unit_of_work import (
    SqlAlchemySchedulerExecutionUnitOfWork,
)
from shell.scheduling_service.infrastructure.scheduling.scheduler_job.persistence.sql.services.scheduler_job_query_service import (
    SchedulerJobQueryService,
)
from shell.scheduling_service.infrastructure.scheduling.scheduler_job.persistence.sql.unit_of_work import (
    SqlAlchemySchedulerJobUnitOfWork,
)


class SchedulingCoreContainer(containers.DeclarativeContainer):
    config = providers.Configuration()
    session_factory = providers.Singleton(build_session_factory, url=config.db_url)
    persistence_delivery_models = providers.Object(PERSISTENCE_DELIVERY_MODELS)
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
    scheduler_definition_uow_factory = providers.Factory(
        SqlAlchemySchedulerDefinitionUnitOfWork,
        session_factory=session_factory,
        mapper=integration_mapper,
        models=persistence_delivery_models,
    )
    scheduler_execution_uow_factory = providers.Factory(
        SqlAlchemySchedulerExecutionUnitOfWork,
        session_factory=session_factory,
        mapper=integration_mapper,
        models=persistence_delivery_models,
    )
    scheduler_job_uow_factory = providers.Factory(
        SqlAlchemySchedulerJobUnitOfWork,
        session_factory=session_factory,
        mapper=integration_mapper,
        models=persistence_delivery_models,
    )
    clock_factory = providers.Factory(SystemClock)
    id_generator_factory = providers.Factory(UuidIdGenerator)
    command_bus = providers.Singleton(CommandBus)
    query_bus = providers.Singleton(QueryBus)
    event_bus = providers.Singleton(EventBus)
    event_registry = providers.Singleton(build_scheduling_event_registry)
    event_inbox_processor_factory = providers.Factory(
        EventInboxProcessor,
        session_factory=session_factory,
        event_bus=event_bus,
        models=persistence_delivery_models.provided.events,
        registry=event_registry,
        worker_id=config.worker_id,
        processed_delivery_model=persistence_delivery_models.provided.processed_delivery,
        consumer_name="scheduling",
        heartbeat_interval_seconds=config.worker_heartbeat_interval_seconds,
        max_batch_time_seconds=config.worker_max_batch_time_seconds,
        envelope_policy=envelope_policy_from_catalog(SCHEDULING_CONTRACT_CATALOG),
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
    command_registry = providers.Object(
        build_command_registry(
            discover_command_types("shell.scheduling_service.application.scheduling")
        )
    )
    command_inbox_processor_factory = providers.Factory(
        CommandInboxProcessor,
        session_factory=session_factory,
        command_bus=command_bus,
        models=persistence_delivery_models.provided.commands,
        registry=command_registry,
        processed_delivery_model=persistence_delivery_models.provided.processed_delivery,
        consumer_name="scheduling-command",
        worker_id=config.command_worker_id,
        heartbeat_interval_seconds=config.worker_heartbeat_interval_seconds,
        max_batch_time_seconds=config.worker_max_batch_time_seconds,
        upcaster=providers.Singleton(PayloadUpcaster),
    )
    rabbit_inbox_consumer_factory = providers.Factory(
        RabbitEventInboxConsumer,
        url=config.broker_url,
        session_factory=session_factory,
        models=persistence_delivery_models.provided.events,
        queue_name="shell-scheduling-event-inbox",
        routing_keys=["event.#"],
    )
    rabbit_command_inbox_consumer_factory = providers.Factory(
        RabbitCommandInboxConsumer,
        url=config.broker_url,
        session_factory=session_factory,
        models=persistence_delivery_models.provided.commands,
        service_name="scheduling",
    )
    scheduler_definition_query_service = providers.Singleton(
        SchedulerDefinitionQueryService, session_factory=session_factory
    )
    scheduler_execution_query_service = providers.Singleton(
        SchedulerExecutionQueryService, session_factory=session_factory
    )
    scheduler_job_query_service = providers.Singleton(
        SchedulerJobQueryService, session_factory=session_factory
    )
    create_scheduler_definition_handler_factory = providers.Factory(
        CreateSchedulerDefinitionHandler,
        unit_of_work=scheduler_definition_uow_factory,
        clock=clock_factory,
        id_generator=id_generator_factory,
    )
    change_scheduler_definition_handler_factory = providers.Factory(
        ChangeSchedulerDefinitionHandler,
        unit_of_work=scheduler_definition_uow_factory,
        clock=clock_factory,
    )
    delete_scheduler_definition_handler_factory = providers.Factory(
        DeleteSchedulerDefinitionHandler,
        unit_of_work=scheduler_definition_uow_factory,
        clock=clock_factory,
    )
    create_scheduler_execution_handler_factory = providers.Factory(
        CreateSchedulerExecutionHandler,
        unit_of_work=scheduler_execution_uow_factory,
        clock=clock_factory,
        id_generator=id_generator_factory,
    )
    change_scheduler_execution_handler_factory = providers.Factory(
        ChangeSchedulerExecutionHandler,
        unit_of_work=scheduler_execution_uow_factory,
        clock=clock_factory,
    )
    delete_scheduler_execution_handler_factory = providers.Factory(
        DeleteSchedulerExecutionHandler,
        unit_of_work=scheduler_execution_uow_factory,
        clock=clock_factory,
    )
    create_scheduler_job_handler_factory = providers.Factory(
        CreateSchedulerJobHandler,
        unit_of_work=scheduler_job_uow_factory,
        clock=clock_factory,
        id_generator=id_generator_factory,
    )
    change_scheduler_job_handler_factory = providers.Factory(
        ChangeSchedulerJobHandler, unit_of_work=scheduler_job_uow_factory, clock=clock_factory
    )
    delete_scheduler_job_handler_factory = providers.Factory(
        DeleteSchedulerJobHandler, unit_of_work=scheduler_job_uow_factory, clock=clock_factory
    )
    get_scheduler_definition_handler_factory = providers.Factory(
        GetSchedulerDefinitionByIdHandler, queries=scheduler_definition_query_service
    )
    get_scheduler_execution_handler_factory = providers.Factory(
        GetSchedulerExecutionByIdHandler, queries=scheduler_execution_query_service
    )
    list_scheduler_executions_handler_factory = providers.Factory(
        ListSchedulerExecutionsHandler, queries=scheduler_execution_query_service
    )
    get_scheduler_job_handler_factory = providers.Factory(
        GetSchedulerJobByIdHandler, queries=scheduler_job_query_service
    )
    list_scheduler_jobs_handler_factory = providers.Factory(
        ListSchedulerJobsHandler, queries=scheduler_job_query_service
    )


def configure_scheduling_container(container: SchedulingCoreContainer) -> None:
    command_bus = container.command_bus()
    query_bus = container.query_bus()
    for command, factory in (
        (CreateSchedulerDefinitionCommand, container.create_scheduler_definition_handler_factory),
        (ChangeSchedulerDefinitionCommand, container.change_scheduler_definition_handler_factory),
        (DeleteSchedulerDefinitionCommand, container.delete_scheduler_definition_handler_factory),
        (CreateSchedulerExecutionCommand, container.create_scheduler_execution_handler_factory),
        (ChangeSchedulerExecutionCommand, container.change_scheduler_execution_handler_factory),
        (DeleteSchedulerExecutionCommand, container.delete_scheduler_execution_handler_factory),
        (CreateSchedulerJobCommand, container.create_scheduler_job_handler_factory),
        (ChangeSchedulerJobCommand, container.change_scheduler_job_handler_factory),
        (DeleteSchedulerJobCommand, container.delete_scheduler_job_handler_factory),
    ):
        command_bus.register(command, factory)
    query_bus.register(
        GetSchedulerDefinitionByIdQuery, container.get_scheduler_definition_handler_factory
    )
    query_bus.register(
        GetSchedulerExecutionByIdQuery, container.get_scheduler_execution_handler_factory
    )
    query_bus.register(
        ListSchedulerExecutionsQuery, container.list_scheduler_executions_handler_factory
    )
    query_bus.register(GetSchedulerJobByIdQuery, container.get_scheduler_job_handler_factory)
    query_bus.register(ListSchedulerJobsQuery, container.list_scheduler_jobs_handler_factory)
