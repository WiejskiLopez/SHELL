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


from .envelope_deadlettered_event import EnvelopeDeadletteredEvent
from .envelope_expired_event import EnvelopeExpiredEvent
from .envelope_routed_event import EnvelopeRoutedEvent
from .graph_execution_built_event import GraphExecutionBuiltEvent
from .graph_node_execution_advanced_event import GraphNodeExecutionAdvancedEvent
from .graph_node_execution_completed_event import GraphNodeExecutionCompletedEvent
from .graph_node_execution_condition_evaluated_event import (
    GraphNodeExecutionConditionEvaluatedEvent,
)
from .graph_node_execution_failed_event import GraphNodeExecutionFailedEvent
from .graph_node_execution_join_ready_event import GraphNodeExecutionJoinReadyEvent
from .graph_node_execution_loop_iteration_event import GraphNodeExecutionLoopIterationEvent
from .graph_node_execution_requested_event import GraphNodeExecutionRequestedEvent
from .graph_node_execution_started_event import GraphNodeExecutionStartedEvent
from .graph_node_execution_timed_out_event import GraphNodeExecutionTimedOutEvent
from .graph_node_parallel_execution_requested_event import (
    GraphNodeParallelExecutionRequestedEvent,
)
from .task_execution_completed_event import TaskExecutionCompletedEvent
from .task_execution_created_event import TaskExecutionCreatedEvent
from .workflow_completed_event import WorkflowCompletedEvent
from .workflow_failed_event import WorkflowFailedEvent
from .workflow_started_event import WorkflowStartedEvent

__all__ = [
    "DomainEvent",
    "EnvelopeDeadletteredEvent",
    "EnvelopeExpiredEvent",
    "EnvelopeRoutedEvent",
    "GraphExecutionBuiltEvent",
    "GraphNodeExecutionAdvancedEvent",
    "GraphNodeExecutionCompletedEvent",
    "GraphNodeExecutionConditionEvaluatedEvent",
    "GraphNodeExecutionFailedEvent",
    "GraphNodeExecutionJoinReadyEvent",
    "GraphNodeExecutionLoopIterationEvent",
    "GraphNodeExecutionRequestedEvent",
    "GraphNodeExecutionStartedEvent",
    "GraphNodeExecutionTimedOutEvent",
    "GraphNodeParallelExecutionRequestedEvent",
    "TaskExecutionCompletedEvent",
    "TaskExecutionCreatedEvent",
    "WorkflowCompletedEvent",
    "WorkflowFailedEvent",
    "WorkflowStartedEvent",
]
