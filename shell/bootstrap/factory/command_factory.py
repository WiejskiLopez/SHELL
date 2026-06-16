"""Rejestracja Command Handlers na CommandBus."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.commands.commands import (
    ArchiveEnvelopeCommand,
    BootstrapRunnerConfigCommand,
    ImportTaskCommand,
    RouteEnvelopesCommand,
    RunNodeCommand,
    RunTaskerWorkflowCommand,
    SaveNodeResultCommand,
    SavePromptCommand,
    StartWorkflowCommand,
)

if TYPE_CHECKING:
    from shell.bootstrap.container.core_container import CoreContainer


def register_commands(core_container: CoreContainer) -> None:
    """Rejestruje wszystkie Command Handlers na CommandBus kontenera."""
    cmd_bus = core_container.app.buses.command_bus()
    cmd_bus.register(ImportTaskCommand, core_container.app.commands.import_task_handler_factory)
    cmd_bus.register(
        StartWorkflowCommand, core_container.app.commands.start_workflow_handler_factory
    )
    cmd_bus.register(
        RouteEnvelopesCommand, core_container.app.commands.route_envelopes_handler_factory
    )
    cmd_bus.register(RunNodeCommand, core_container.app.commands.run_node_handler_factory)
    cmd_bus.register(
        ArchiveEnvelopeCommand, core_container.app.commands.archive_envelope_handler_factory
    )
    cmd_bus.register(
        SaveNodeResultCommand, core_container.app.commands.save_node_result_handler_factory
    )
    cmd_bus.register(SavePromptCommand, core_container.app.commands.save_prompt_handler_factory)
    cmd_bus.register(
        BootstrapRunnerConfigCommand,
        core_container.app.commands.bootstrap_runner_config_handler_factory,
    )
    cmd_bus.register(
        RunTaskerWorkflowCommand, core_container.app.commands.run_tasker_workflow_handler_factory
    )
