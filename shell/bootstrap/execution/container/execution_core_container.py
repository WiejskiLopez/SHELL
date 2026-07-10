"""ExecutionCoreContainer — minimalny kontener DI dla mikroserwisu Execution BC."""

from __future__ import annotations

from dependency_injector import containers, providers

from shell.application.execution.edge_execution.command_handlers.create_edge_execution_handler import (
    CreateEdgeExecutionHandler,
)
from shell.application.execution.edge_execution.command_handlers.delete_edge_execution_handler import (
    DeleteEdgeExecutionHandler,
)
from shell.application.execution.edge_execution.command_handlers.update_edge_execution_handler import (
    UpdateEdgeExecutionHandler,
)
from shell.application.execution.edge_link_execution.command_handlers.create_edge_link_execution_handler import (
    CreateEdgeLinkExecutionHandler,
)
from shell.application.execution.edge_link_execution.command_handlers.delete_edge_link_execution_handler import (
    DeleteEdgeLinkExecutionHandler,
)
from shell.application.execution.edge_link_execution.command_handlers.update_edge_link_execution_handler import (
    UpdateEdgeLinkExecutionHandler,
)
from shell.application.execution.node_execution.command_handlers.create_node_execution_handler import (
    CreateNodeExecutionHandler,
)
from shell.infrastructure.execution.edge_execution.persistence.sql.unit_of_work import (
    SqlAlchemyEdgeExecutionUnitOfWork,
)
from shell.infrastructure.execution.edge_link_execution.persistence.sql.unit_of_work import (
    SqlAlchemyEdgeLinkExecutionUnitOfWork,
)
from shell.infrastructure.execution.node_execution.persistence.sql.services.node_result_query_service import (
    NodeResultQueryService,
)
from shell.infrastructure.execution.node_execution.persistence.sql.unit_of_work import (
    SqlAlchemyNodeExecutionUnitOfWork,
)
from shell.infrastructure.execution.session_execution.persistence.sql.services.session_query_service import (
    SessionQueryService,
)
from shell.infrastructure.execution.task_execution.persistence.sql.services.task_execution_query_service import (
    TaskExecutionQueryService,
)
from shell.infrastructure.execution.workflow.persistence.sql.services.workflow_query_service import (
    WorkflowQueryService,
)
from shell.platform.application.bus.command_bus import CommandBus
from shell.platform.application.bus.query_bus import QueryBus
from shell.platform.infrastructure.identity.uuid_id_generator import UuidIdGenerator
from shell.platform.infrastructure.logging.stdlib_logger import StdlibLogger
from shell.platform.infrastructure.persistence.sql import build_session_factory
from shell.platform.infrastructure.time.system_clock import SystemClock


class ExecutionCoreContainer(containers.DeclarativeContainer):
    """Minimalny kontener dla BC Execution — używany przy starcie mikroserwisu execution."""

    config = providers.Configuration()

    # Infrastruktura bazodanowa
    session_factory = providers.Singleton(build_session_factory, url=config.db_url)

    # Per-aggregate Unit of Work — każdy agregat ma własny UoW
    edge_execution_uow_factory = providers.Factory(
        SqlAlchemyEdgeExecutionUnitOfWork,
        session_factory=session_factory,
    )
    edge_link_execution_uow_factory = providers.Factory(
        SqlAlchemyEdgeLinkExecutionUnitOfWork,
        session_factory=session_factory,
    )
    node_execution_uow_factory = providers.Factory(
        SqlAlchemyNodeExecutionUnitOfWork,
        session_factory=session_factory,
    )

    # Narzędzia wspólne
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
