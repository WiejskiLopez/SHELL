"""Kontener obsługujący wyłącznie operacje zapisu (Command Handlers)."""

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
from shell.application.user.user.command_handlers.create_user_handler import CreateUserHandler
from shell.application.user.user.command_handlers.delete_user_handler import DeleteUserHandler
from shell.application.user.user.command_handlers.login_user_handler import LoginUserHandler
from shell.application.user.user.command_handlers.update_user_handler import UpdateUserHandler


class CommandContainer(containers.DeclarativeContainer):
    """Container handling write operations only (Command Handlers)."""

    config = providers.Configuration()
    infra = providers.DependenciesContainer()
    domain = providers.DependenciesContainer()
    buses = providers.DependenciesContainer()

    create_node_execution_handler_factory = providers.Factory(
        CreateNodeExecutionHandler,
        unit_of_work=buses.unit_of_work_factory,
        identity=infra.id_generator_factory,
        time=infra.clock_factory,
    )

    create_edge_execution_handler_factory = providers.Factory(
        CreateEdgeExecutionHandler,
        unit_of_work=buses.unit_of_work_factory,
        identity=infra.id_generator_factory,
        time=infra.clock_factory,
    )
    update_edge_execution_handler_factory = providers.Factory(
        UpdateEdgeExecutionHandler,
        unit_of_work=buses.unit_of_work_factory,
        time=infra.clock_factory,
        logger=infra.stdlib_logger,
    )
    delete_edge_execution_handler_factory = providers.Factory(
        DeleteEdgeExecutionHandler,
        unit_of_work=buses.unit_of_work_factory,
        time=infra.clock_factory,
        logger=infra.stdlib_logger,
    )

    create_edge_link_execution_handler_factory = providers.Factory(
        CreateEdgeLinkExecutionHandler,
        unit_of_work=buses.unit_of_work_factory,
        identity=infra.id_generator_factory,
        time=infra.clock_factory,
    )
    delete_edge_link_execution_handler_factory = providers.Factory(
        DeleteEdgeLinkExecutionHandler,
        unit_of_work=buses.unit_of_work_factory,
        time=infra.clock_factory,
        logger=infra.stdlib_logger,
    )
    update_edge_link_execution_handler_factory = providers.Factory(
        UpdateEdgeLinkExecutionHandler,
        unit_of_work=buses.unit_of_work_factory,
        time=infra.clock_factory,
        logger=infra.stdlib_logger,
    )

    create_user_handler_factory = providers.Factory(
        CreateUserHandler,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
        id_generator=infra.id_generator_factory,
    )
    login_user_handler_factory = providers.Factory(
        LoginUserHandler,
        unit_of_work=buses.unit_of_work_factory,
        queries=infra.user_query_service,
        clock=infra.clock_factory,
    )
    update_user_handler_factory = providers.Factory(
        UpdateUserHandler,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
    )
    delete_user_handler_factory = providers.Factory(
        DeleteUserHandler,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
    )
