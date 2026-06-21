"""Execution repository ports."""

from __future__ import annotations

from shell.domain.execution.aggregates.envelope.ports.envelope_archive import EnvelopeArchive
from shell.domain.execution.aggregates.envelope.ports.envelope_repository import EnvelopeRepository
from shell.domain.execution.aggregates.graph_execution.ports.graph_execution_repository import (
    GraphExecutionRepository,
)
from shell.domain.execution.aggregates.graph_node_execution.ports.graph_node_execution_repository import (
    GraphNodeExecutionRepository,
)
from shell.domain.execution.aggregates.session.ports.session_repository import SessionRepository
from shell.domain.execution.aggregates.task_execution.ports.task_execution_repository import (
    TaskExecutionRepository,
)
from shell.domain.execution.aggregates.task_execution_state_input.ports.task_execution_state_input_repository import (
    TaskExecutionStateInputRepository,
)
from shell.domain.execution.aggregates.task_execution_state_output.ports.task_execution_state_output_repository import (
    TaskExecutionStateOutputRepository,
)
from shell.domain.execution.aggregates.workflow.ports.workflow_repository import WorkflowRepository

__all__ = [
    "EnvelopeArchive",
    "EnvelopeRepository",
    "GraphExecutionRepository",
    "GraphNodeExecutionRepository",
    "SessionRepository",
    "TaskExecutionStateInputRepository",
    "TaskExecutionStateOutputRepository",
    "TaskExecutionRepository",
    "WorkflowRepository",
]
