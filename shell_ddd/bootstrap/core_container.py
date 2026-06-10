"""Główny kontener DI - łączy wszystkie handlery, porty i adaptery."""
from __future__ import annotations

from dependency_injector import containers, providers

from shell_ddd.application.bus.command_bus import CommandBus
from shell_ddd.application.bus.event_bus import EventBus
from shell_ddd.application.bus.event_bus_publisher import EventBusPublisher
from shell_ddd.application.bus.query_bus import QueryBus

from shell_ddd.infrastructure.persistence.sql.query_services import SqlQueryServices
from shell_ddd.infrastructure.persistence.sql import build_session_factory
from shell_ddd.infrastructure.persistence import SqlAlchemyUnitOfWork

from shell_ddd.infrastructure.external.hash_embedder import HashEmbedder
from shell_ddd.infrastructure.time.system_clock import SystemClock
from shell_ddd.shared.ids import UuidIdGenerator
from shell_ddd.infrastructure.logging.stdlib_logger import StdlibLogger
from shell_ddd.infrastructure.logging.composite_event_publisher import CompositeEventPublisher
from shell_ddd.infrastructure.logging.logging_event_publisher import LoggingEventPublisher
from shell_ddd.infrastructure.logging.sql_audit_publisher import SqlAuditPublisher
from shell_ddd.infrastructure.process.subprocess_runner import SubprocessNodeProcessRunner
from shell_ddd.infrastructure.filesystem.node_workspace import NodeWorkspaceFs
from shell_ddd.infrastructure.filesystem.task_loader import FileSystemTaskLoader

from shell_ddd.application.strategies.node_execution_strategy import get_strategy

from shell_ddd.application.command_handlers.archive_envelope_handler import ArchiveEnvelopeHandler
from shell_ddd.application.command_handlers.bootstrap_runner_config_handler import BootstrapRunnerConfigHandler
from shell_ddd.application.command_handlers.import_task_handler import ImportTaskHandler
from shell_ddd.application.command_handlers.route_envelopes_handler import RouteEnvelopesHandler
from shell_ddd.application.command_handlers.run_node_handler import RunNodeHandler
from shell_ddd.application.command_handlers.run_tasker_workflow_handler import RunTaskerWorkflowHandler
from shell_ddd.application.command_handlers.save_node_result_handler import SaveNodeResultHandler
from shell_ddd.application.command_handlers.save_prompt_handler import SavePromptHandler
from shell_ddd.application.command_handlers.start_workflow_handler import StartWorkflowHandler

from shell_ddd.application.event_handlers.event_handlers import ArchiveOnDeliveredHandler, LogAuditHandler
from shell_ddd.application.event_handlers.workflow_execution_worker import WorkflowExecutionWorker

from shell_ddd.application.query_handlers.query_handlers import (
    GetCurrentTaskHandler,
    GetEnvelopesByWorkflowHandler,
    GetNodeResultHandler,
    GetPromptHandler,
    GetRunnerConfigHandler,
    GetTaskByNameHandler,
    GetWorkflowHandler,
    GetSessionHistoryHandler,
    SearchSimilarHandler,
)


class CoreContainer(containers.DeclarativeContainer):
    """Główny kontener DI aplikacji."""

    config = providers.Configuration()

    # 1. Singletony (Infrastruktura współdzielona)
    session_factory = providers.Singleton(
        build_session_factory,
        url=config.db_url
    )

    query_services = providers.Singleton(
        SqlQueryServices,
        session_factory=session_factory
    )

    stdlib_logger = providers.Singleton(StdlibLogger, name="shell_ddd")
    embedder = providers.Singleton(HashEmbedder)

    command_bus = providers.Singleton(CommandBus)
    query_bus = providers.Singleton(QueryBus)
    event_bus = providers.Singleton(EventBus)

    # Mechanizm publikacji zdarzeń
    logging_publisher = providers.Singleton(LoggingEventPublisher, logger=stdlib_logger)
    sql_audit_publisher = providers.Singleton(SqlAuditPublisher, session_factory=session_factory)
    bus_publisher = providers.Singleton(EventBusPublisher, event_bus=event_bus)

    event_publisher = providers.Singleton(
        CompositeEventPublisher,
        publishers=providers.List(logging_publisher, sql_audit_publisher, bus_publisher)
    )

    strategy = providers.Object(get_strategy("agent"))

    # 2. Factories (Tworzone od nowa per Request - bezpieczne dla współbieżności)
    uow_factory = providers.Factory(
        SqlAlchemyUnitOfWork,
        session_factory=session_factory
    )

    clock_factory = providers.Factory(SystemClock)
    id_gen_factory = providers.Factory(UuidIdGenerator)
    task_loader_factory = providers.Factory(FileSystemTaskLoader)
    workspace_factory = providers.Factory(NodeWorkspaceFs)
    runner_factory = providers.Factory(SubprocessNodeProcessRunner)

    # 3. Command Handlers (Każde odwołanie to NOWA instancja i nowy UoW)
    import_task_handler_factory = providers.Factory(
        ImportTaskHandler, uow=uow_factory, clock=clock_factory, id_gen=id_gen_factory, task_loader=task_loader_factory, event_publisher=event_publisher, logger=stdlib_logger
    )
    start_workflow_handler_factory = providers.Factory(
        StartWorkflowHandler, uow=uow_factory, clock=clock_factory, id_gen=id_gen_factory, event_publisher=event_publisher
    )
    route_envelopes_handler_factory = providers.Factory(
        RouteEnvelopesHandler, uow=uow_factory, clock=clock_factory, event_publisher=event_publisher, max_step=config.max_step
    )
    run_node_handler_factory = providers.Factory(
        RunNodeHandler, uow=uow_factory, clock=clock_factory, id_gen=id_gen_factory, workspace=workspace_factory, runner=runner_factory, strategy=strategy,
        event_publisher=event_publisher
    )
    archive_envelope_handler_factory = providers.Factory(
        ArchiveEnvelopeHandler, uow=uow_factory, clock=clock_factory, event_publisher=event_publisher
    )
    save_node_result_handler_factory = providers.Factory(
        SaveNodeResultHandler, uow=uow_factory, clock=clock_factory, id_gen=id_gen_factory, event_publisher=event_publisher
    )
    save_prompt_handler_factory = providers.Factory(
        SavePromptHandler, uow=uow_factory, clock=clock_factory, id_gen=id_gen_factory
    )
    bootstrap_runner_config_handler_factory = providers.Factory(
        BootstrapRunnerConfigHandler, uow=uow_factory, clock=clock_factory, id_gen=id_gen_factory
    )
    run_tasker_workflow_handler_factory = providers.Factory(
        RunTaskerWorkflowHandler, uow=uow_factory, clock=clock_factory, id_gen=id_gen_factory, event_publisher=event_publisher
    )
    workflow_execution_worker_factory = providers.Factory(
        WorkflowExecutionWorker, uow=uow_factory, clock=clock_factory, id_gen=id_gen_factory, runner=runner_factory, event_publisher=event_publisher
    )

    # 4. Query Handlers (Factories)
    get_task_by_name_handler_factory = providers.Factory(GetTaskByNameHandler, queries=query_services)
    get_current_task_handler_factory = providers.Factory(GetCurrentTaskHandler, queries=query_services)
    get_workflow_handler_factory = providers.Factory(GetWorkflowHandler, queries=query_services)
    get_envelopes_by_workflow_handler_factory = providers.Factory(GetEnvelopesByWorkflowHandler, queries=query_services)
    get_node_result_handler_factory = providers.Factory(GetNodeResultHandler, queries=query_services)
    get_prompt_handler_factory = providers.Factory(GetPromptHandler, queries=query_services)
    get_runner_config_handler_factory = providers.Factory(GetRunnerConfigHandler, queries=query_services)
    get_session_history_handler_factory = providers.Factory(GetSessionHistoryHandler, queries=query_services)
    search_similar_handler_factory = providers.Factory(SearchSimilarHandler, queries=query_services, embedder=embedder)

    # 5. Event Handlers (Factories — subskrybenci EventBus)
    archive_on_delivered_handler_factory = providers.Factory(
        ArchiveOnDeliveredHandler, uow=uow_factory
    )
    log_audit_handler_factory = providers.Factory(
        LogAuditHandler, logger=stdlib_logger
    )
