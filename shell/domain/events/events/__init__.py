"""Domain events for shell."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True, kw_only=True)
class DomainEvent:
    occurred_at: datetime
    schema_version: int = 1

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        """Metoda fabryczna wymuszona dla każdego eventu."""
        raise NotImplementedError


from .envelope_expired import EnvelopeExpired
from .envelope_routed import EnvelopeRouted
from .graph_execution_built import GraphExecutionBuilt
from .graph_node_execution_advanced import GraphNodeExecutionAdvanced
from .graph_node_execution_completed import GraphNodeExecutionCompleted
from .graph_node_execution_failed import GraphNodeExecutionFailed
from .graph_node_execution_requested import GraphNodeExecutionRequested
from .graph_node_execution_started import GraphNodeExecutionStarted
from .task_execution_completed import TaskExecutionCompleted
from .task_execution_created import TaskExecutionCreated
from .workflow_completed import WorkflowCompleted
from .workflow_failed import WorkflowFailed
from .workflow_started import WorkflowStarted

__all__ = [
    "DomainEvent",
    "EnvelopeExpired",
    "EnvelopeRouted",
    "GraphExecutionBuilt",
    "GraphNodeExecutionAdvanced",
    "GraphNodeExecutionCompleted",
    "GraphNodeExecutionFailed",
    "GraphNodeExecutionRequested",
    "GraphNodeExecutionStarted",
    "TaskExecutionCompleted",
    "TaskExecutionCreated",
    "WorkflowCompleted",
    "WorkflowFailed",
    "WorkflowStarted",
]
