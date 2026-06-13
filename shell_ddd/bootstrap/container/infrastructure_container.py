"""Kontener zarządzający adapterami wejścia/wyjścia, bazą danych i portami."""
from __future__ import annotations

from dependency_injector import containers, providers

from shell_ddd.infrastructure.external.hash_embedder import HashEmbedder
from shell_ddd.infrastructure.filesystem.node_workspace import NodeWorkspaceFs
from shell_ddd.infrastructure.filesystem.task_loader import FileSystemTaskLoader
from shell_ddd.infrastructure.logging.logging_event_publisher import LoggingEventPublisher
from shell_ddd.infrastructure.logging.sql_audit_publisher import SqlAuditPublisher
from shell_ddd.infrastructure.logging.stdlib_logger import StdlibLogger
from shell_ddd.infrastructure.persistence import SqlAlchemyUnitOfWork
from shell_ddd.infrastructure.persistence.sql import build_session_factory
from shell_ddd.infrastructure.persistence.sql.query_services import SqlQueryServices
from shell_ddd.infrastructure.process.subprocess_runner import SubprocessNodeProcessRunner
from shell_ddd.infrastructure.time.system_clock import SystemClock
from shell_ddd.shared.ids import UuidIdGenerator


class InfrastructureContainer(containers.DeclarativeContainer):
    """Kontener zarządzający adapterami wejścia/wyjścia, bazą i portami."""

    config = providers.Configuration()

    # 1. Baza danych i UoW
    session_factory = providers.Singleton(build_session_factory, url=config.db_url)
    query_services = providers.Singleton(SqlQueryServices, session_factory=session_factory)
    uow_factory = providers.Factory(SqlAlchemyUnitOfWork, session_factory=session_factory)

    # 2. Narzędzia i adaptery portów
    stdlib_logger = providers.Singleton(StdlibLogger, name="shell_ddd")
    embedder = providers.Singleton(HashEmbedder)
    clock_factory = providers.Factory(SystemClock)
    id_gen_factory = providers.Factory(UuidIdGenerator)
    task_loader_factory = providers.Factory(FileSystemTaskLoader)
    workspace_factory = providers.Factory(NodeWorkspaceFs)
    runner_factory = providers.Factory(SubprocessNodeProcessRunner)

    # 3. Publikatory zdarzeń (warstwa IO)
    logging_publisher = providers.Singleton(LoggingEventPublisher, logger=stdlib_logger)
    sql_audit_publisher = providers.Singleton(SqlAuditPublisher, session_factory=session_factory)