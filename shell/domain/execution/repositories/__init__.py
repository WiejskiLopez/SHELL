"""Execution repository ports."""

from __future__ import annotations

from shell.domain.execution.aggregates.envelope.ports.envelope_archive import EnvelopeArchive
from shell.domain.execution.aggregates.envelope.repositories.envelope_repository import EnvelopeRepository
from shell.domain.execution.aggregates.graph_execution.repositories.graph_execution_repository import (
    GraphExecutionRepository,
)
from shell.domain.execution.aggregates.graph_execution_state.repositories.graph_execution_state_repository import (
    GraphExecutionStateRepository,
)
from shell.domain.execution.aggregates.graph_node_execution.repositories.graph_node_execution_repository import (
    GraphNodeExecutionRepository,
)
from shell.domain.execution.aggregates.task_execution.repositories.task_execution_repository import (
    TaskExecutionRepository,
)
from shell.domain.execution.aggregates.task_execution_state.repositories.task_execution_state_repository import (
    TaskExecutionStateRepository,
)
from shell.domain.execution.aggregates.workflow.repositories.workflow_repository import WorkflowRepository

__all__ = [
    "EnvelopeArchive",
    "EnvelopeRepository",
    "GraphExecutionRepository",
    "GraphExecutionStateRepository",
    "GraphNodeExecutionRepository",
    "TaskExecutionStateRepository",
    "TaskExecutionRepository",
    "WorkflowRepository",
]
