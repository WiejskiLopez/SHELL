"""ExecutionCoreContainer — minimal DI container for the Execution BC microservice."""

from __future__ import annotations

from dependency_injector import containers, providers

from shell.execution.application.execution.edge_execution.command_handlers.create_edge_execution_handler import (
    CreateEdgeExecutionHandler,
)
from shell.execution.application.execution.edge_execution.command_handlers.delete_edge_execution_handler import (
    DeleteEdgeExecutionHandler,
)
from shell.execution.application.execution.edge_execution.command_handlers.update_edge_execution_handler import (
    UpdateEdgeExecutionHandler,
)
from shell.execution.application.execution.edge_execution.queries.get_edge_execution_by_id_query import (
    GetEdgeExecutionByIdQuery,
)
from shell.execution.application.execution.edge_execution.query_handlers.get_edge_execution_by_id_handler import (
    GetEdgeExecutionByIdHandler,
)
from shell.execution.application.execution.edge_link_execution.command_handlers.create_edge_link_execution_handler import (
    CreateEdgeLinkExecutionHandler,
)
from shell.execution.application.execution.edge_link_execution.command_handlers.delete_edge_link_execution_handler import (
    DeleteEdgeLinkExecutionHandler,
)
from shell.execution.application.execution.edge_link_execution.command_handlers.update_edge_link_execution_handler import (
    UpdateEdgeLinkExecutionHandler,
)
from shell.execution.application.execution.edge_link_execution.queries.get_edge_link_execution_by_id_query import (
    GetEdgeLinkExecutionByIdQuery,
)
from shell.execution.application.execution.edge_link_execution.query_handlers.get_edge_link_execution_by_id_handler import (
    GetEdgeLinkExecutionByIdHandler,
)
from shell.execution.application.execution.node_execution.command_handlers.create_node_execution_handler import (
    CreateNodeExecutionHandler,
)
from shell.execution.application.execution.node_execution.queries.get_node_execution_result_query import (
    GetNodeExecutionResultQuery,
)
from shell.execution.application.execution.node_execution.query_handlers.get_node_execution_result_handler import (
    GetNodeExecutionResultHandler,
)
from shell.execution.application.execution.task_execution.queries.list_task_executions_query import (
    ListTaskExecutionsQuery,
)
from shell.execution.application.execution.task_execution.query_handlers.list_task_executions_handler import (
    ListTaskExecutionsHandler,
)
from shell.execution.application.execution.workflow.command_handlers.create_workflow_handler import (
    CreateWorkflowHandler,
)
from shell.execution.application.execution.workflow.command_handlers.delete_workflow_handler import (
    DeleteWorkflowHandler,
)
from shell.execution.application.execution.workflow.command_handlers.update_workflow_handler import (
    UpdateWorkflowHandler,
)
from shell.execution.application.execution.workflow.commands.create_workflow_command import (
    CreateWorkflowCommand,
)
from shell.execution.application.execution.workflow.commands.delete_workflow_command import (
    DeleteWorkflowCommand,
)
from shell.execution.application.execution.workflow.commands.update_workflow_command import (
    UpdateWorkflowCommand,
)
from shell.execution.application.execution.workflow.queries.get_workflow_by_id_query import (
    GetWorkflowByIdQuery,
)
from shell.execution.application.execution.workflow.queries.list_workflows_query import (
    ListWorkflowsQuery,
)
from shell.execution.application.execution.workflow.query_handlers.get_workflow_by_id_handler import (
    GetWorkflowByIdHandler,
)
from shell.execution.application.execution.workflow.query_handlers.list_workflows_handler import (
    ListWorkflowsHandler,
)
from shell.execution.bootstrap.execution.contract_catalog import EXECUTION_CONTRACT_CATALOG
from shell.execution.bootstrap.execution.event_registry import build_execution_event_registry
from shell.execution.bootstrap.execution.upcaster import build_execution_upcaster
from shell.execution.infrastructure.execution.edge_execution.persistence.sql.services.edge_execution_query_service import (
    EdgeExecutionQueryService,
)
from shell.execution.infrastructure.execution.edge_execution.persistence.sql.unit_of_work import (
    SqlAlchemyEdgeExecutionUnitOfWork,
)
from shell.execution.infrastructure.execution.edge_link_execution.persistence.sql.services.edge_link_execution_query_service import (
    EdgeLinkExecutionQueryService,
)
from shell.execution.infrastructure.execution.edge_link_execution.persistence.sql.unit_of_work import (
    SqlAlchemyEdgeLinkExecutionUnitOfWork,
)
from shell.execution.infrastructure.execution.node_execution.persistence.sql.services.node_result_query_service import (
    NodeResultQueryService,
)
from shell.execution.infrastructure.execution.node_execution.persistence.sql.unit_of_work import (
    SqlAlchemyNodeExecutionUnitOfWork,
)
from shell.execution.infrastructure.execution.persistence.sql.models.base import (
    PERSISTENCE_DELIVERY_MODELS,
)
from shell.execution.infrastructure.execution.task_execution.persistence.sql.services.task_execution_query_service import (
    TaskExecutionQueryService,
)
from shell.execution.infrastructure.execution.task_execution.persistence.sql.unit_of_work import (
    SqlAlchemyTaskExecutionUnitOfWork,
)
from shell.execution.infrastructure.execution.workflow.persistence.sql.services.workflow_query_service import (
    WorkflowQueryService,
)
from shell.execution.infrastructure.execution.workflow.persistence.sql.unit_of_work import (
    SqlAlchemyWorkflowUnitOfWork,
)
from shell.platform.application.bus.command_bus import CommandBus
from shell.platform.application.bus.event_bus import EventBus
from shell.platform.application.bus.query_bus import QueryBus
from shell.platform.infrastructure.health.sql_readiness_probe import SqlReadinessProbe
from shell.platform.infrastructure.identity.uuid_id_generator import UuidIdGenerator
from shell.platform.infrastructure.logging.stdlib_logger import StdlibLogger
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


class ExecutionCoreContainer(containers.DeclarativeContainer):
    """Minimal container for BC Execution — used when starting the execution microservice."""

    config = providers.Configuration()

    # Infrastruktura bazodanowa
    session_factory = providers.Singleton(build_session_factory, url=config.db_url)
    command_bus = providers.Singleton(CommandBus)

    # Per-aggregate Unit of Work — każdy agregat ma własny UoW
    persistence_delivery_models = providers.Object(PERSISTENCE_DELIVERY_MODELS)
    event_bus = providers.Singleton(EventBus)
    event_registry = providers.Singleton(build_execution_event_registry)
    event_inbox_processor_factory = providers.Factory(
        EventInboxProcessor,
        session_factory=session_factory,
        event_bus=event_bus,
        models=persistence_delivery_models.provided.events,
        registry=event_registry,
        processed_delivery_model=persistence_delivery_models.provided.processed_delivery,
        consumer_name="execution",
        worker_id=config.worker_id,
        heartbeat_interval_seconds=config.worker_heartbeat_interval_seconds,
        max_batch_time_seconds=config.worker_max_batch_time_seconds,
        envelope_policy=envelope_policy_from_catalog(EXECUTION_CONTRACT_CATALOG),
        upcaster=providers.Singleton(build_execution_upcaster),
    )
    command_registry = providers.Object(
        build_command_registry(
            discover_command_types("shell.execution.application.execution")
        )
    )
    command_inbox_processor_factory = providers.Factory(
        CommandInboxProcessor,
        session_factory=session_factory,
        command_bus=command_bus,
        models=persistence_delivery_models.provided.commands,
        registry=command_registry,
        processed_delivery_model=persistence_delivery_models.provided.processed_delivery,
        consumer_name="execution-command",
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
        queue_name="shell-execution-command-inbox",
        routing_keys=["command.#"],
    )
    rabbit_inbox_consumer_factory = providers.Factory(
        RabbitInboxConsumer,
        url=config.broker_url,
        session_factory=session_factory,
        models=persistence_delivery_models.provided.events,
        queue_name="shell-execution-event-inbox",
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
    edge_execution_uow_factory = providers.Factory(
        SqlAlchemyEdgeExecutionUnitOfWork,
        session_factory=session_factory,
        models=persistence_delivery_models,
    )
    edge_link_execution_uow_factory = providers.Factory(
        SqlAlchemyEdgeLinkExecutionUnitOfWork,
        session_factory=session_factory,
        models=persistence_delivery_models,
    )
    node_execution_uow_factory = providers.Factory(
        SqlAlchemyNodeExecutionUnitOfWork,
        session_factory=session_factory,
        models=persistence_delivery_models,
    )

    # Shared tools
    clock_factory = providers.Factory(SystemClock)
    id_generator_factory = providers.Factory(UuidIdGenerator)
    stdlib_logger = providers.Singleton(StdlibLogger, name="shell.execution")
    # Query services (read-only, bez UoW)
    task_execution_query_service = providers.Singleton(
        TaskExecutionQueryService, session_factory=session_factory
    )
    workflow_query_service = providers.Singleton(
        WorkflowQueryService, session_factory=session_factory
    )
    edge_link_execution_query_service = providers.Singleton(
        EdgeLinkExecutionQueryService, session_factory=session_factory
    )
    get_edge_link_execution_handler_factory = providers.Factory(
        GetEdgeLinkExecutionByIdHandler, queries=edge_link_execution_query_service
    )
    workflow_uow_factory = providers.Factory(
        SqlAlchemyWorkflowUnitOfWork,
        session_factory=session_factory,
        models=persistence_delivery_models,
    )
    task_execution_uow_factory = providers.Factory(
        SqlAlchemyTaskExecutionUnitOfWork,
        session_factory=session_factory,
        models=persistence_delivery_models,
    )
    create_workflow_handler_factory = providers.Factory(
        CreateWorkflowHandler,
        unit_of_work=workflow_uow_factory,
        clock=clock_factory,
        id_generator=id_generator_factory,
    )
    update_workflow_handler_factory = providers.Factory(
        UpdateWorkflowHandler, unit_of_work=workflow_uow_factory, clock=clock_factory
    )
    delete_workflow_handler_factory = providers.Factory(
        DeleteWorkflowHandler, unit_of_work=workflow_uow_factory, clock=clock_factory
    )
    get_workflow_handler_factory = providers.Factory(
        GetWorkflowByIdHandler, queries=workflow_query_service
    )
    list_workflows_handler_factory = providers.Factory(
        ListWorkflowsHandler, queries=workflow_query_service
    )
    list_task_executions_handler_factory = providers.Factory(
        ListTaskExecutionsHandler, queries=task_execution_query_service
    )
    node_result_query_service = providers.Singleton(
        NodeResultQueryService, session_factory=session_factory
    )
    get_node_execution_result_handler_factory = providers.Factory(
        GetNodeExecutionResultHandler, queries=node_result_query_service
    )
    edge_execution_query_service = providers.Singleton(
        EdgeExecutionQueryService, session_factory=session_factory
    )
    get_edge_execution_handler_factory = providers.Factory(
        GetEdgeExecutionByIdHandler, queries=edge_execution_query_service
    )

    # Application buses
    query_bus = providers.Singleton(QueryBus)

    # Command Handlers — tylko Execution BC
    create_node_execution_handler_factory = providers.Factory(
        CreateNodeExecutionHandler,
        unit_of_work=node_execution_uow_factory,
        identity=id_generator_factory,
        time=clock_factory,
    )
    create_edge_execution_handler_factory = providers.Factory(
        CreateEdgeExecutionHandler,
        unit_of_work=edge_execution_uow_factory,
        identity=id_generator_factory,
        time=clock_factory,
    )
    update_edge_execution_handler_factory = providers.Factory(
        UpdateEdgeExecutionHandler,
        unit_of_work=edge_execution_uow_factory,
        time=clock_factory,
        logger=stdlib_logger,
    )
    delete_edge_execution_handler_factory = providers.Factory(
        DeleteEdgeExecutionHandler,
        unit_of_work=edge_execution_uow_factory,
        time=clock_factory,
        logger=stdlib_logger,
    )
    create_edge_link_execution_handler_factory = providers.Factory(
        CreateEdgeLinkExecutionHandler,
        unit_of_work=edge_link_execution_uow_factory,
        identity=id_generator_factory,
        time=clock_factory,
    )
    delete_edge_link_execution_handler_factory = providers.Factory(
        DeleteEdgeLinkExecutionHandler,
        unit_of_work=edge_link_execution_uow_factory,
        time=clock_factory,
        logger=stdlib_logger,
    )
    update_edge_link_execution_handler_factory = providers.Factory(
        UpdateEdgeLinkExecutionHandler,
        unit_of_work=edge_link_execution_uow_factory,
        time=clock_factory,
        logger=stdlib_logger,
    )


def configure_execution_container(container: ExecutionCoreContainer) -> None:
    from shell.execution.application.execution.edge_execution.commands.create_edge_execution_command import (
        CreateEdgeExecutionCommand,
    )
    from shell.execution.application.execution.edge_execution.commands.delete_edge_execution_command import (
        DeleteEdgeExecutionCommand,
    )
    from shell.execution.application.execution.edge_execution.commands.update_edge_execution_command import (
        UpdateEdgeExecutionCommand,
    )
    from shell.execution.application.execution.edge_link_execution.commands.create_edge_link_execution_command import (
        CreateEdgeLinkExecutionCommand,
    )
    from shell.execution.application.execution.edge_link_execution.commands.delete_edge_link_execution_command import (
        DeleteEdgeLinkExecutionCommand,
    )
    from shell.execution.application.execution.edge_link_execution.commands.update_edge_link_execution_command import (
        UpdateEdgeLinkExecutionCommand,
    )
    from shell.execution.application.execution.node_execution.commands.create_node_execution_command import (
        CreateNodeExecutionCommand,
    )

    command_bus = container.command_bus()
    query_bus = container.query_bus()
    for command, factory in (
        (CreateEdgeExecutionCommand, container.create_edge_execution_handler_factory),
        (UpdateEdgeExecutionCommand, container.update_edge_execution_handler_factory),
        (DeleteEdgeExecutionCommand, container.delete_edge_execution_handler_factory),
        (CreateEdgeLinkExecutionCommand, container.create_edge_link_execution_handler_factory),
        (DeleteEdgeLinkExecutionCommand, container.delete_edge_link_execution_handler_factory),
        (UpdateEdgeLinkExecutionCommand, container.update_edge_link_execution_handler_factory),
        (CreateNodeExecutionCommand, container.create_node_execution_handler_factory),
        (CreateWorkflowCommand, container.create_workflow_handler_factory),
        (UpdateWorkflowCommand, container.update_workflow_handler_factory),
        (DeleteWorkflowCommand, container.delete_workflow_handler_factory),
    ):
        command_bus.register(command, factory)
    query_bus.register(GetEdgeExecutionByIdQuery, container.get_edge_execution_handler_factory)
    query_bus.register(
        GetEdgeLinkExecutionByIdQuery, container.get_edge_link_execution_handler_factory
    )
    query_bus.register(GetWorkflowByIdQuery, container.get_workflow_handler_factory)
    query_bus.register(ListWorkflowsQuery, container.list_workflows_handler_factory)
    query_bus.register(ListTaskExecutionsQuery, container.list_task_executions_handler_factory)
    query_bus.register(
        GetNodeExecutionResultQuery, container.get_node_execution_result_handler_factory
    )
