"""ExecutionCoreContainer — minimalny kontener DI dla mikroserwisu Execution BC."""

from __future__ import annotations

from dependency_injector import containers, providers

from shell.application.execution.edge_execution.command_handlers.edge_execution_create_handler import (
    EdgeExecutionCreateHandler,
)
from shell.application.execution.edge_execution.command_handlers.edge_execution_delete_handler import (
    EdgeExecutionDeleteHandler,
)
from shell.application.execution.edge_execution.command_handlers.edge_execution_update_handler import (
    EdgeExecutionUpdateHandler,
)
from shell.application.execution.edge_link_execution.command_handlers.edge_link_execution_create_handler import (
    EdgeLinkExecutionCreateHandler,
)
from shell.application.execution.edge_link_execution.command_handlers.edge_link_execution_delete_handler import (
    EdgeLinkExecutionDeleteHandler,
)
from shell.application.execution.edge_link_execution.command_handlers.edge_link_execution_update_handler import (
    EdgeLinkExecutionUpdateHandler,
)
from shell.application.execution.node_execution.command_handlers.node_execution_create_handler import (
    NodeExecutionCreateHandler,
)
from shell.application.platform.bus.command_bus import CommandBus
from shell.application.platform.bus.query_bus import QueryBus
from shell.infrastructure.execution.node_execution.filesystem.workspace import Workspace
from shell.infrastructure.execution.persistence.sql.services import (
    NodeResultQueryService,
    SessionQueryService,
    TaskExecutionQueryService,
    WorkflowQueryService,
)
from shell.infrastructure.execution.persistence.sql_alchemy_execution_uow import (
    SqlAlchemyExecutionUnitOfWork,
)
from shell.infrastructure.execution.process.subprocess_runner import (
    SubprocessNodeExecutionProcessRunner,
)
from shell.infrastructure.platform.identity.uuid_id_generator import UuidIdGenerator
from shell.infrastructure.platform.logging.stdlib_logger import StdlibLogger
from shell.infrastructure.platform.persistence.sql import build_session_factory
from shell.infrastructure.platform.time.system_clock import SystemClock


class ExecutionCoreContainer(containers.DeclarativeContainer):
    """Minimalny kontener dla BC Execution — używany przy starcie mikroserwisu execution."""

    config = providers.Configuration()

    # Infrastruktura bazodanowa
    session_factory = providers.Singleton(build_session_factory, url=config.db_url)

    # Per-BC Unit of Work — zna TYLKO repozytoria BC Execution
    unit_of_work_factory = providers.Factory(
        SqlAlchemyExecutionUnitOfWork,
        session_factory=session_factory,
    )

    # Narzędzia wspólne
    clock_factory = providers.Factory(SystemClock)
    id_generator_factory = providers.Factory(UuidIdGenerator)
    stdlib_logger = providers.Singleton(StdlibLogger, name="shell.execution")
    workspace_factory = providers.Factory(Workspace)
    runner_factory = providers.Factory(SubprocessNodeExecutionProcessRunner)

    # Query services (read-only, bez UoW)
    task_execution_query_service = providers.Singleton(
        TaskExecutionQueryService, session_factory=session_factory
    )
    workflow_query_service = providers.Singleton(
        WorkflowQueryService, session_factory=session_factory
    )
    node_result_query_service = providers.Singleton(
        NodeResultQueryService, session_factory=session_factory
    )
    session_query_service = providers.Singleton(
        SessionQueryService, session_factory=session_factory
    )

    # Szyny aplikacyjne
    command_bus = providers.Singleton(CommandBus)
    query_bus = providers.Singleton(QueryBus)

    # Command Handlers — tylko Execution BC
    create_node_execution_handler_factory = providers.Factory(
        NodeExecutionCreateHandler,
        unit_of_work=unit_of_work_factory,
        identity=id_generator_factory,
        time=clock_factory,
    )
    edge_execution_create_handler_factory = providers.Factory(
        EdgeExecutionCreateHandler,
        unit_of_work=unit_of_work_factory,
        identity=id_generator_factory,
        time=clock_factory,
    )
    edge_execution_update_handler_factory = providers.Factory(
        EdgeExecutionUpdateHandler,
        unit_of_work=unit_of_work_factory,
        time=clock_factory,
        logger=stdlib_logger,
    )
    edge_execution_delete_handler_factory = providers.Factory(
        EdgeExecutionDeleteHandler,
        unit_of_work=unit_of_work_factory,
        time=clock_factory,
        logger=stdlib_logger,
    )
    edge_link_execution_create_handler_factory = providers.Factory(
        EdgeLinkExecutionCreateHandler,
        unit_of_work=unit_of_work_factory,
        identity=id_generator_factory,
        time=clock_factory,
    )
    edge_link_execution_delete_handler_factory = providers.Factory(
        EdgeLinkExecutionDeleteHandler,
        unit_of_work=unit_of_work_factory,
        time=clock_factory,
        logger=stdlib_logger,
    )
    edge_link_execution_update_handler_factory = providers.Factory(
        EdgeLinkExecutionUpdateHandler,
        unit_of_work=unit_of_work_factory,
        time=clock_factory,
        logger=stdlib_logger,
    )
