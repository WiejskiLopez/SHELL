"""Application commands — re-exports from granular modules (backward compatibility)."""
from __future__ import annotations

from shell_ddd.application.commands.config_commands import BootstrapRunnerConfigCommand
from shell_ddd.application.commands.envelope_commands import ArchiveEnvelopeCommand
from shell_ddd.application.commands.node_commands import RunNodeCommand, SaveNodeResultCommand
from shell_ddd.application.commands.prompt_commands import SavePromptCommand
from shell_ddd.application.commands.rag_commands import IndexDocumentCommand
from shell_ddd.application.commands.session_commands import AppendMessageCommand, CloseSessionCommand, OpenSessionCommand
from shell_ddd.application.commands.task_commands import ImportTaskCommand
from shell_ddd.application.commands.workflow_commands import RouteEnvelopesCommand, RunTaskerWorkflowCommand, StartWorkflowCommand

__all__ = [
    "AppendMessageCommand",
    "ArchiveEnvelopeCommand",
    "BootstrapRunnerConfigCommand",
    "CloseSessionCommand",
    "ImportTaskCommand",
    "IndexDocumentCommand",
    "OpenSessionCommand",
    "RouteEnvelopesCommand",
    "RunNodeCommand",
    "RunTaskerWorkflowCommand",
    "SaveNodeResultCommand",
    "SavePromptCommand",
    "StartWorkflowCommand",
]