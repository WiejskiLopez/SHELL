"""Kontener zarządzający adapterami wejścia/wyjścia, bazą danych i portami."""

from __future__ import annotations

from dependency_injector import containers, providers

from shell.infrastructure.definition.graph_definition.persistence.sql.services.graph_definition_query_service import (
    SqlGraphDefinitionQueryService,
)
from shell.infrastructure.definition.rag_document.persistence.sql.services.rag_query_service import (
    RagQueryService,
)
from shell.infrastructure.definition.runner_config.persistence.sql.services.runner_config_query_service import (
    RunnerConfigQueryService,
)
from shell.infrastructure.execution.graph_execution.http.graph_execution_definition_provider_http_adapter import (
    GraphExecutionDefinitionProviderHttpAdapter,
)
from shell.infrastructure.execution.node_execution.filesystem.workspace import Workspace
from shell.infrastructure.execution.node_execution.persistence.sql.services.node_result_query_service import (
    NodeResultQueryService,
)
from shell.infrastructure.execution.process.subprocess_runner import (
    SubprocessNodeExecutionProcessRunner,
)
from shell.infrastructure.execution.session_execution.http.session_query_service_http_adapter import (
    SessionQueryServiceHttpAdapter,
)
from shell.infrastructure.execution.session_execution.persistence.sql.services.session_query_service import (
    SessionQueryService,
)
from shell.infrastructure.execution.task_execution.filesystem.task_execution_loader import (
    FileSystemTaskLoader,
)
from shell.infrastructure.execution.task_execution.persistence.sql.services.task_execution_query_service import (
    TaskExecutionQueryService,
)
from shell.infrastructure.execution.workflow.persistence.sql.services.workflow_query_service import (
    WorkflowQueryService,
)
from shell.infrastructure.platform.context.client import CorrelationIdAsyncClient
from shell.infrastructure.platform.external.hash_embedder import HashEmbedder
from shell.infrastructure.platform.identity.uuid_id_generator import UuidIdGenerator
from shell.infrastructure.platform.logging.logging_event_publisher import LoggingEventPublisher
from shell.infrastructure.platform.logging.sql_audit_publisher import SqlAuditPublisher
from shell.infrastructure.platform.logging.stdlib_logger import StdlibLogger
from shell.infrastructure.platform.messaging.command.sql_command_outbox_publisher import (
    SqlCommandOutboxPublisher,
)
from shell.infrastructure.platform.persistence import SqlAlchemyUnitOfWork
from shell.infrastructure.platform.persistence.sql import build_session_factory
from shell.infrastructure.platform.time.system_clock import SystemClock
from shell.infrastructure.session.session.http.workflow_session_provider_http_adapter import (
    WorkflowSessionProviderHttpAdapter,
)


class InfrastructureContainer(containers.DeclarativeContainer):
    """Kontener zarządzający adapterami wejścia/wyjścia, bazą i portami."""

    config = providers.Configuration()

    # 1. Baza danych i UoW
    session_factory = providers.Singleton(build_session_factory, url=config.db_url)
    task_execution_query_service = providers.Singleton(
        TaskExecutionQueryService, session_factory=session_factory
    )
    workflow_query_service = providers.Singleton(
        WorkflowQueryService, session_factory=session_factory
    )
    node_result_query_service = providers.Singleton(
        NodeResultQueryService, session_factory=session_factory
    )
    runner_config_query_service = providers.Singleton(
        RunnerConfigQueryService, session_factory=session_factory
    )
    session_query_service = providers.Singleton(
        SessionQueryService, session_factory=session_factory
    )
    rag_query_service = providers.Singleton(RagQueryService, session_factory=session_factory)
    unit_of_work_factory = providers.Factory(SqlAlchemyUnitOfWork, session_factory=session_factory)

    # 2. Narzędzia i adaptery portów
    stdlib_logger = providers.Singleton(StdlibLogger, name="shell")
    embedder = providers.Singleton(HashEmbedder)
    clock_factory = providers.Factory(SystemClock)
    id_generator_factory = providers.Factory(UuidIdGenerator)
    task_execution_loader_factory = providers.Factory(FileSystemTaskLoader)
    workspace_factory = providers.Factory(Workspace)
    runner_factory = providers.Factory(SubprocessNodeExecutionProcessRunner)

    # 3. SQL query services (internal use by each BC's own REST API / handlers)
    graph_definition_query_service_factory = providers.Factory(
        SqlGraphDefinitionQueryService,
        session_factory=session_factory,
        embedder=embedder,
    )

    # 4. HTTP clients for cross-BC communication
    definition_http_client = providers.Singleton(
        CorrelationIdAsyncClient,
        base_url=config.definition_api_url,
    )
    execution_http_client = providers.Singleton(
        CorrelationIdAsyncClient,
        base_url=config.execution_api_url,
    )
    session_http_client = providers.Singleton(
        CorrelationIdAsyncClient,
        base_url=config.session_api_url,
    )
    user_http_client = providers.Singleton(
        CorrelationIdAsyncClient,
        base_url=config.user_api_url,
    )
    project_http_client = providers.Singleton(
        CorrelationIdAsyncClient,
        base_url=config.project_api_url,
    )

    # 5. Cross-BC HTTP adapters (bridge execution → other BCs via REST API)
    definition_provider_factory = providers.Factory(
        GraphExecutionDefinitionProviderHttpAdapter,
        client=definition_http_client,
    )
    session_query_http_service = providers.Factory(
        SessionQueryServiceHttpAdapter,
        client=session_http_client,
    )
    workflow_session_provider_factory = providers.Factory(
        WorkflowSessionProviderHttpAdapter,
        client=execution_http_client,
    )
    sql_command_outbox_publisher_factory = providers.Singleton(
        SqlCommandOutboxPublisher,
        session_factory=session_factory,
    )

    # 8. Publikatory zdarzeń (warstwa IO)
    logging_publisher = providers.Singleton(LoggingEventPublisher, logger=stdlib_logger)
    sql_audit_publisher = providers.Singleton(SqlAuditPublisher, session_factory=session_factory)
