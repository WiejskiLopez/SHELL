"""Application commands — re-exports from granular modules (backward compatibility)."""

from __future__ import annotations

from shell.application.definition.commands.config_commands import BootstrapRunnerConfigCommand
from shell.application.definition.commands.rag_commands import IndexDocumentCommand
from shell.application.execution.commands.envelope_commands import ArchiveEnvelopeCommand
from shell.application.execution.commands.graph_node_execution_commands import (
    RunGraphNodeExecutionCommand,
    SaveGraphNodeExecutionResultCommand,
)
from shell.application.execution.commands.session_commands import (
    CloseSessionCommand,
    OpenSessionCommand,
)
from shell.application.execution.commands.task_execution_commands import ImportTaskExecutionCommand
from shell.application.execution.commands.workflow_commands import (
    RouteEnvelopesCommand,
    RunTaskerWorkflowCommand,
    StartWorkflowCommand,
)

__all__ = [
    "ArchiveEnvelopeCommand",
    "BootstrapRunnerConfigCommand",
    "CloseSessionCommand",
    "ImportTaskExecutionCommand",
    "IndexDocumentCommand",
    "OpenSessionCommand",
    "RouteEnvelopesCommand",
    "RunGraphNodeExecutionCommand",
    "RunTaskerWorkflowCommand",
    "SaveGraphNodeExecutionResultCommand",
    "StartWorkflowCommand",
]
