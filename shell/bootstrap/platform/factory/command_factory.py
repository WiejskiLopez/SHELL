"""Rejestracja Command Handlers na CommandBus."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any  # Dodano import Any

from shell.application.platform.commands.commands import (
    ArchiveEnvelopeCommand,
    BootstrapRunnerConfigCommand,
    ImportTaskExecutionCommand,
    RouteEnvelopesCommand,
    RunGraphNodeExecutionCommand,
    RunTaskerWorkflowCommand,
    SaveGraphNodeExecutionResultCommand,
    SavePromptCommand,
    StartWorkflowCommand,
)

if TYPE_CHECKING:
    from shell.bootstrap.platform.container.core_container import CoreContainer


def register_commands(core_container: CoreContainer) -> None:
    """Rejestruje wszystkie Command Handlers na CommandBus kontenera."""

    # Wyciągamy podkontener do zmiennej typu Any.
    # Uciszamy mypy tylko RAZ w tym miejscu.
    app_ctx: Any = core_container.app  # type: ignore[attr-defined]

    cmd_bus = app_ctx.buses.command_bus()
    commands = app_ctx.commands

    # Rejestracja handlerów staje się czysta, krótka i w pełni czytelna:
    cmd_bus.register(ImportTaskExecutionCommand, commands.import_task_execution_handler_factory)
    cmd_bus.register(StartWorkflowCommand, commands.start_workflow_handler_factory)
    cmd_bus.register(RouteEnvelopesCommand, commands.route_envelopes_handler_factory)
    cmd_bus.register(
        RunGraphNodeExecutionCommand, commands.run_graph_node_execution_handler_factory
    )
    cmd_bus.register(ArchiveEnvelopeCommand, commands.archive_envelope_handler_factory)
    cmd_bus.register(
        SaveGraphNodeExecutionResultCommand,
        commands.save_graph_node_execution_result_handler_factory,
    )
    cmd_bus.register(SavePromptCommand, commands.save_prompt_handler_factory)
    cmd_bus.register(
        BootstrapRunnerConfigCommand,
        commands.bootstrap_runner_config_handler_factory,
    )
    cmd_bus.register(RunTaskerWorkflowCommand, commands.run_tasker_workflow_handler_factory)
