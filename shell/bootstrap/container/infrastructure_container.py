"""Kontener zarządzający adapterami wejścia/wyjścia, bazą danych i portami."""

from __future__ import annotations

from dependency_injector import containers, providers

from shell.infrastructure.external.hash_embedder import HashEmbedder
from shell.infrastructure.filesystem.task_execution_loader import FileSystemTaskLoader
from shell.infrastructure.filesystem.workspace import Workspace
from shell.infrastructure.logging.logging_event_publisher import LoggingEventPublisher
from shell.infrastructure.logging.sql_audit_publisher import SqlAuditPublisher
from shell.infrastructure.logging.stdlib_logger import StdlibLogger
from shell.infrastructure.persistence import SqlAlchemyUnitOfWork
from shell.infrastructure.persistence.sql import build_session_factory
from shell.infrastructure.persistence.sql.services import (
    EnvelopeQueryService,
    NodeResultQueryService,
    PromptQueryService,
    RagQueryService,
    RunnerConfigQueryService,
    SessionQueryService,
    TaskExecutionQueryService,
    WorkflowQueryService,
)
from shell.infrastructure.process.subprocess_runner import SubprocessNodeProcessRunner
from shell.infrastructure.time.system_clock import SystemClock
from shell.infrastructure.identity.uuid_id_generator import UuidIdGenerator


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
    envelope_query_service = providers.Singleton(
        EnvelopeQueryService, session_factory=session_factory
    )
    node_result_query_service = providers.Singleton(
        NodeResultQueryService, session_factory=session_factory
    )
    prompt_query_service = providers.Singleton(
        PromptQueryService, session_factory=session_factory
    )
    runner_config_query_service = providers.Singleton(
        RunnerConfigQueryService, session_factory=session_factory
    )
    session_query_service = providers.Singleton(
        SessionQueryService, session_factory=session_factory
    )
    rag_query_service = providers.Singleton(
        RagQueryService, session_factory=session_factory
    )
    uow_factory = providers.Factory(SqlAlchemyUnitOfWork, session_factory=session_factory)

    # 2. Narzędzia i adaptery portów
    stdlib_logger = providers.Singleton(StdlibLogger, name="shell")
    embedder = providers.Singleton(HashEmbedder)
    clock_factory = providers.Factory(SystemClock)
    id_gen_factory = providers.Factory(UuidIdGenerator)
    task_execution_loader_factory = providers.Factory(FileSystemTaskLoader)
    workspace_factory = providers.Factory(Workspace)
    runner_factory = providers.Factory(SubprocessNodeProcessRunner)

    # 3. Publikatory zdarzeń (warstwa IO)
    logging_publisher = providers.Singleton(LoggingEventPublisher, logger=stdlib_logger)
    sql_audit_publisher = providers.Singleton(SqlAuditPublisher, session_factory=session_factory)
