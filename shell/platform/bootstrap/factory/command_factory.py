"""Rejestracja Command Handlers na CommandBus."""

from __future__ import annotations

from typing import TYPE_CHECKING

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
    from shell.platform.bootstrap.container.core_container import Container


def register_commands(container: Container) -> None:
    """Rejestruje wszystkie Command Handlers na CommandBus kontenera."""

    cmd_bus = container.app.buses.command_bus
    commands = container.app.commands

    cmd_bus.register(
        CreateNodeExecutionCommand,
        commands.create_node_execution_handler_factory,
    )

    cmd_bus.register(
        CreateEdgeExecutionCommand,
        commands.create_edge_execution_handler_factory,
    )
    cmd_bus.register(
        UpdateEdgeExecutionCommand,
        commands.update_edge_execution_handler_factory,
    )
    cmd_bus.register(
        DeleteEdgeExecutionCommand,
        commands.delete_edge_execution_handler_factory,
    )

    cmd_bus.register(
        CreateEdgeLinkExecutionCommand,
        commands.create_edge_link_execution_handler_factory,
    )
    cmd_bus.register(
        DeleteEdgeLinkExecutionCommand,
        commands.delete_edge_link_execution_handler_factory,
    )
    cmd_bus.register(
        UpdateEdgeLinkExecutionCommand,
        commands.update_edge_link_execution_handler_factory,
    )

    cmd_bus.register(CreateUserCommand, commands.create_user_handler_factory)
    cmd_bus.register(UpdateUserCommand, commands.update_user_handler_factory)
    cmd_bus.register(DeleteUserCommand, commands.delete_user_handler_factory)
