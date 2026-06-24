"""Execution repository ports."""

from __future__ import annotations

from shell.domain.execution.aggregates.envelope.ports.envelope_archive import EnvelopeArchive
from shell.domain.execution.aggregates.envelope.repositories.envelope_repository import EnvelopeRepository
from shell.domain.execution.aggregates.graph_execution.repositories.graph_execution_repository import (
    GraphExecutionRepository,
)
from shell.domain.execution.aggregates.graph_node_execution.repositories.graph_node_execution_repository import (
    GraphNodeExecutionRepository,
)
from shell.domain.execution.aggregates.session.repositories.session_repository import SessionRepository
from shell.domain.execution.aggregates.task_execution.repositories.task_execution_repository import (
    TaskExecutionRepository,
)
from shell.domain.execution.aggregates.task_execution_state_input.repositories.task_execution_state_input_repository import (
    TaskExecutionStateInputRepository,
)
from shell.domain.execution.aggregates.task_execution_state_output.repositories.task_execution_state_output_repository import (
    TaskExecutionStateOutputRepository,
)
from shell.domain.execution.aggregates.workflow.repositories.workflow_repository import WorkflowRepository

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
