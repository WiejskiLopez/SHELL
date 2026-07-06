"""Kontener obsługujący wyłącznie operacje zapisu (Command Handlers)."""

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
from shell.application.user.user.command_handlers.user_create_handler import UserCreateHandler
from shell.application.user.user.command_handlers.user_delete_handler import UserDeleteHandler
from shell.application.user.user.command_handlers.user_update_handler import UserUpdateHandler


class CommandContainer(containers.DeclarativeContainer):
    """Kontener obsługujący wyłącznie operacje zapisu (Command Handlers)."""

    config = providers.Configuration()
    infra = providers.DependenciesContainer()
    domain = providers.DependenciesContainer()
    buses = providers.DependenciesContainer()

    create_node_execution_handler_factory = providers.Factory(
        NodeExecutionCreateHandler,
        unit_of_work=buses.unit_of_work_factory,
        identity=infra.id_generator_factory,
        time=infra.clock_factory,
    )

    edge_execution_create_handler_factory = providers.Factory(
        EdgeExecutionCreateHandler,
        unit_of_work=buses.unit_of_work_factory,
        identity=infra.id_generator_factory,
        time=infra.clock_factory,
    )
    edge_execution_update_handler_factory = providers.Factory(
        EdgeExecutionUpdateHandler,
        unit_of_work=buses.unit_of_work_factory,
        time=infra.clock_factory,
        logger=infra.stdlib_logger,
    )
    edge_execution_delete_handler_factory = providers.Factory(
        EdgeExecutionDeleteHandler,
        unit_of_work=buses.unit_of_work_factory,
        time=infra.clock_factory,
        logger=infra.stdlib_logger,
    )

    edge_link_execution_create_handler_factory = providers.Factory(
        EdgeLinkExecutionCreateHandler,
        unit_of_work=buses.unit_of_work_factory,
        identity=infra.id_generator_factory,
        time=infra.clock_factory,
    )
    edge_link_execution_delete_handler_factory = providers.Factory(
        EdgeLinkExecutionDeleteHandler,
        unit_of_work=buses.unit_of_work_factory,
        time=infra.clock_factory,
        logger=infra.stdlib_logger,
    )
    edge_link_execution_update_handler_factory = providers.Factory(
        EdgeLinkExecutionUpdateHandler,
        unit_of_work=buses.unit_of_work_factory,
        time=infra.clock_factory,
        logger=infra.stdlib_logger,
    )

    create_user_handler_factory = providers.Factory(
        UserCreateHandler,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
        id_generator=infra.id_generator_factory,
    )
    update_user_handler_factory = providers.Factory(
        UserUpdateHandler,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
    )
    delete_user_handler_factory = providers.Factory(
        UserDeleteHandler,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
    )
