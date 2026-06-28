"""Rejestracja Command Handlers na CommandBus."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any  # Dodano import Any

from shell.application.definition.commands.create_graph_definition_command import (
    CreateGraphDefinitionCommand,
)
from shell.application.execution.commands.attach_graph_node_executions_command import (
    AttachGraphNodeExecutionsCommand,
)
from shell.application.execution.commands.create_graph_node_execution_command import (
    CreateGraphNodeExecutionCommand,
)
from shell.application.definition.commands.config_commands import BootstrapRunnerConfigCommand
from shell.application.execution.commands.task_execution_commands import ImportTaskExecutionCommand
from shell.application.execution.commands.graph_node_execution_commands import RunGraphNodeExecutionCommand
from shell.application.execution.commands.workflow_commands import RunTaskerWorkflowCommand
from shell.application.execution.commands.graph_node_execution_commands import SaveGraphNodeExecutionResultCommand
from shell.application.execution.commands.workflow_commands import StartWorkflowCommand

if TYPE_CHECKING:
    from shell.bootstrap.platform.container.core_container import CoreContainer


def register_commands(core_container: CoreContainer) -> None:
    """Rejestruje wszystkie Command Handlers na CommandBus kontenera."""

    app_ctx: Any = core_container.app

    cmd_bus = app_ctx.buses.command_bus()
    commands = app_ctx.commands

    cmd_bus.register(
        CreateGraphDefinitionCommand, commands.create_graph_definition_handler_factory,
    )
    cmd_bus.register(ImportTaskExecutionCommand, commands.import_task_execution_handler_factory)
    cmd_bus.register(StartWorkflowCommand, commands.start_workflow_handler_factory)
    cmd_bus.register(
        RunGraphNodeExecutionCommand, commands.run_graph_node_execution_handler_factory
    )
    cmd_bus.register(
        SaveGraphNodeExecutionResultCommand,
        commands.save_graph_node_execution_result_handler_factory,
    )
    cmd_bus.register(
        BootstrapRunnerConfigCommand,
        commands.bootstrap_runner_config_handler_factory,
    )
    cmd_bus.register(RunTaskerWorkflowCommand, commands.run_tasker_workflow_handler_factory)
    cmd_bus.register(
        CreateGraphNodeExecutionCommand,
        commands.create_graph_node_execution_handler_factory,
    )
    cmd_bus.register(
        AttachGraphNodeExecutionsCommand,
        commands.attach_graph_node_executions_handler_factory,
    )
