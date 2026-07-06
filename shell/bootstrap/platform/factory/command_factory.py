"""Rejestracja Command Handlers na CommandBus."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any  # Dodano import Any

from shell.application.execution.edge_execution.commands.create_edge_execution_command import (
    CreateEdgeExecutionCommand,
)
from shell.application.execution.edge_execution.commands.delete_edge_execution_command import (
    DeleteEdgeExecutionCommand,
)
from shell.application.execution.edge_execution.commands.update_edge_execution_command import (
    UpdateEdgeExecutionCommand,
)
from shell.application.execution.edge_link_execution.commands.create_edge_link_execution_command import (
    CreateEdgeLinkExecutionCommand,
)
from shell.application.execution.edge_link_execution.commands.delete_edge_link_execution_command import (
    DeleteEdgeLinkExecutionCommand,
)
from shell.application.execution.edge_link_execution.commands.update_edge_link_execution_command import (
    UpdateEdgeLinkExecutionCommand,
)
from shell.application.execution.node_execution.commands.create_node_execution_command import (
    CreateNodeExecutionCommand,
)
from shell.application.user.user.commands.create_user_command import CreateUserCommand
from shell.application.user.user.commands.delete_user_command import DeleteUserCommand
from shell.application.user.user.commands.update_user_command import UpdateUserCommand

if TYPE_CHECKING:
    from shell.bootstrap.platform.container.core_container import CoreContainer


def register_commands(core_container: CoreContainer) -> None:
    """Rejestruje wszystkie Command Handlers na CommandBus kontenera."""

    app_ctx: Any = core_container.app

    cmd_bus = app_ctx.buses.command_bus()
    commands = app_ctx.commands

    cmd_bus.register(
        CreateNodeExecutionCommand,
        commands.create_node_execution_handler_factory,
    )

    cmd_bus.register(
        CreateEdgeExecutionCommand,
        commands.edge_execution_create_handler_factory,
    )
    cmd_bus.register(
        UpdateEdgeExecutionCommand,
        commands.edge_execution_update_handler_factory,
    )
    cmd_bus.register(
        DeleteEdgeExecutionCommand,
        commands.edge_execution_delete_handler_factory,
    )

    cmd_bus.register(
        CreateEdgeLinkExecutionCommand,
        commands.edge_link_execution_create_handler_factory,
    )
    cmd_bus.register(
        DeleteEdgeLinkExecutionCommand,
        commands.edge_link_execution_delete_handler_factory,
    )
    cmd_bus.register(
        UpdateEdgeLinkExecutionCommand,
        commands.edge_link_execution_update_handler_factory,
    )

    cmd_bus.register(CreateUserCommand, commands.create_user_handler_factory)
    cmd_bus.register(UpdateUserCommand, commands.update_user_handler_factory)
    cmd_bus.register(DeleteUserCommand, commands.delete_user_handler_factory)
