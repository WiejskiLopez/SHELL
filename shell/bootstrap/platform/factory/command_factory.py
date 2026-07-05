"""Rejestracja Command Handlers na CommandBus."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any  # Dodano import Any

from shell.application.definition.commands.config_commands import BootstrapRunnerConfigCommand
from shell.application.definition.commands.create_graph_definition_command import (
    CreateGraphDefinitionCommand,
)
from shell.application.execution.commands.attach_node_executions_command import (
    AttachNodeExecutionsCommand,
)
from shell.application.execution.commands.create_edge_execution_command import (
    CreateEdgeExecutionCommand,
)
from shell.application.execution.commands.create_edge_link_execution_command import (
    CreateEdgeLinkExecutionCommand,
)
from shell.application.execution.commands.create_node_execution_command import (
    CreateNodeExecutionCommand,
)
from shell.application.execution.commands.delete_edge_execution_command import (
    DeleteEdgeExecutionCommand,
)
from shell.application.execution.commands.delete_edge_link_execution_command import (
    DeleteEdgeLinkExecutionCommand,
)
from shell.application.execution.commands.node_execution_commands import (
    RunNodeExecutionCommand,
    SaveNodeExecutionResultCommand,
)
from shell.application.execution.commands.task_execution_commands import ImportTaskExecutionCommand
from shell.application.execution.commands.update_edge_execution_command import (
    UpdateEdgeExecutionCommand,
)
from shell.application.execution.commands.update_edge_link_execution_command import (
    UpdateEdgeLinkExecutionCommand,
)
from shell.application.execution.commands.workflow_commands import (
    RunTaskerWorkflowCommand,
    StartWorkflowCommand,
)
from shell.application.user.commands.create_user_command import CreateUserCommand
from shell.application.user.commands.delete_user_command import DeleteUserCommand
from shell.application.user.commands.update_user_command import UpdateUserCommand

if TYPE_CHECKING:
    from shell.bootstrap.platform.container.core_container import CoreContainer


def register_commands(core_container: CoreContainer) -> None:
    """Rejestruje wszystkie Command Handlers na CommandBus kontenera."""

    app_ctx: Any = core_container.app

    cmd_bus = app_ctx.buses.command_bus()
    commands = app_ctx.commands

    cmd_bus.register(
        CreateGraphDefinitionCommand,
        commands.create_graph_definition_handler_factory,
    )
    cmd_bus.register(ImportTaskExecutionCommand, commands.import_task_execution_handler_factory)
    cmd_bus.register(StartWorkflowCommand, commands.start_workflow_handler_factory)
    cmd_bus.register(
        RunNodeExecutionCommand, commands.run_node_execution_handler_factory
    )
    cmd_bus.register(
        SaveNodeExecutionResultCommand,
        commands.save_node_execution_result_handler_factory,
    )
    cmd_bus.register(
        BootstrapRunnerConfigCommand,
        commands.bootstrap_runner_config_handler_factory,
    )
    cmd_bus.register(RunTaskerWorkflowCommand, commands.run_tasker_workflow_handler_factory)
    cmd_bus.register(
        CreateNodeExecutionCommand,
        commands.create_node_execution_handler_factory,
    )
    cmd_bus.register(
        AttachNodeExecutionsCommand,
        commands.attach_node_executions_handler_factory,
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
