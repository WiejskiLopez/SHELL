"""WorkflowTransitionService — decides next step after a node execution result.

Encapsulates the workflow transition logic extracted from
GraphNodeExecutionCompletedHandler.  Stateless — all data comes from
parameters.  Returns decision value objects that the caller translates
into infrastructure calls (staging events, saving aggregates).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.execution.services.graph_node_execution_policy import (
    AbortDecision as PolicyAbortDecision,
    ContinueDecision,
)
from shell.domain.execution.value_objects.edge_type import EdgeType

if TYPE_CHECKING:
    from collections.abc import Iterable

    from shell.domain.execution.aggregates.graph_execution import GraphExecution
    from shell.domain.execution.aggregates.graph_execution.entities.graph_node_transition_execution import (
        GraphNodeTransitionExecution,
    )
    from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
        GraphNodeExecutionId,
    )
    from shell.domain.execution.aggregates.workflow import Workflow
    from shell.domain.execution.services.graph_node_execution_policy import (
        GraphNodeExecutionPolicy,
    )


# ── Decision value objects ────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class LoopDecision:
    """Continue looping — execute the loop target node."""
    target_node_execution_id: GraphNodeExecutionId


@dataclass(frozen=True, slots=True)
class AdvanceOrFinishSignal:
    """Use navigator to find the next node; finish if none."""


@dataclass(frozen=True, slots=True)
class ErrorHandlerDecision:
    """Route to error handler node."""
    target_node_execution_id: GraphNodeExecutionId


@dataclass(frozen=True, slots=True)
class AbortWorkflowDecision:
    """Workflow aborted due to unrecoverable failure."""
    reason: str


CompletedNodeDecision = LoopDecision | AdvanceOrFinishSignal
FailedNodeDecision = ErrorHandlerDecision | AdvanceOrFinishSignal | AbortWorkflowDecision


# ── Domain Service ────────────────────────────────────────────────────


class WorkflowTransitionService:
    """Decides the next workflow step after a node completes or fails.

    Stateless — all data flows through method parameters.
    """

    @staticmethod
    def decide_after_completed(
        *,
        graph_execution: GraphExecution,
        graph_node_execution_id: GraphNodeExecutionId,
    ) -> CompletedNodeDecision:
        outgoing = graph_execution.get_outgoing_transitions(graph_node_execution_id)
        if not outgoing:
            return AdvanceOrFinishSignal()

        transition_types = {t.transition_type for t in outgoing}
        if EdgeType.LOOP in transition_types:
            return WorkflowTransitionService._evaluate_loop(
                graph_execution=graph_execution,
                outgoing=outgoing,
            )

        return AdvanceOrFinishSignal()

    @staticmethod
    def _evaluate_loop(
        *,
        graph_execution: GraphExecution,
        outgoing: Iterable[GraphNodeTransitionExecution],
    ) -> CompletedNodeDecision:
        loop_transition: GraphNodeTransitionExecution | None = None
        for t in outgoing:
            if t.transition_type == EdgeType.LOOP:
                loop_transition = t
                break

        if loop_transition is None:
            return AdvanceOrFinishSignal()

        counter = graph_execution.increment_loop_counter(
            transition_id=loop_transition.id.value,
            max_loop_count=loop_transition.max_loop_count or 0,
        )

        if not counter.is_exhausted:
            return LoopDecision(target_node_execution_id=loop_transition.target_node_execution_id)

        return AdvanceOrFinishSignal()

    @staticmethod
    def decide_after_failure(
        *,
        graph_execution: GraphExecution,
        graph_node_execution_id: GraphNodeExecutionId,
        workflow: Workflow,
        reason: str,
        policy: GraphNodeExecutionPolicy,
    ) -> FailedNodeDecision:
        outgoing = graph_execution.get_outgoing_transitions(graph_node_execution_id)
        for t in outgoing:
            if t.transition_type == EdgeType.ERROR_HANDLER:
                return ErrorHandlerDecision(target_node_execution_id=t.target_node_execution_id)

        policy_decision = policy.decide_after_failure(workflow, graph_node_execution_id, reason)
        if isinstance(policy_decision, ContinueDecision):
            return AdvanceOrFinishSignal()

        abort_reason = (
            policy_decision.reason
            if isinstance(policy_decision, PolicyAbortDecision)
            else reason
        )
        return AbortWorkflowDecision(reason=abort_reason)
