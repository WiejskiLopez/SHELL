"""WorkflowTransitionService — decides next step after a node execution result.

Stateless — all data flows through method parameters.
Returns decision value objects that the caller translates
into infrastructure calls (staging events, saving aggregates).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.execution.services.graph_node_execution_policy import (
    AbortDecision as PolicyAbortDecision,
)
from shell.domain.execution.services.graph_node_execution_policy import (
    ContinueDecision,
)
from shell.domain.execution.value_objects.edge_type import EdgeType

if TYPE_CHECKING:
    from collections.abc import Sequence

    from shell.domain.execution.aggregates.graph_execution.value_objects.transition_definition import (
        TransitionDefinition,
    )
    from shell.domain.execution.aggregates.graph_node_transition_execution.graph_node_transition_execution import (
        GraphNodeTransitionExecution,
    )
    from shell.domain.execution.services.graph_node_execution_policy import (
        GraphNodeExecutionPolicy,
    )


# ── Decision value objects ────────────────────────────────────────────


@dataclass(frozen=True, slots=True)
class LoopDecision:
    target_node_execution_id: str


@dataclass(frozen=True, slots=True)
class AdvanceOrFinishSignal:
    pass


@dataclass(frozen=True, slots=True)
class ErrorHandlerDecision:
    target_node_execution_id: str


@dataclass(frozen=True, slots=True)
class AbortWorkflowDecision:
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
        outgoing_transitions: Sequence[TransitionDefinition],
        loop_transition_execution: GraphNodeTransitionExecution | None = None,
    ) -> CompletedNodeDecision:
        """Decide what to do after a node completes successfully.

        Args:
            outgoing_transitions: Transition definitions outgoing from the completed node.
            loop_transition_execution: The GraphNodeTransitionExecution aggregate
                for a LOOP transition, if one exists. Used to check loop exhaustion.
        """
        if not outgoing_transitions:
            return AdvanceOrFinishSignal()

        transition_types = {t.edge_type for t in outgoing_transitions}
        if EdgeType.LOOP in transition_types:
            return WorkflowTransitionService._evaluate_loop(
                outgoing=outgoing_transitions,
                loop_transition_execution=loop_transition_execution,
            )

        return AdvanceOrFinishSignal()

    @staticmethod
    def _evaluate_loop(
        *,
        outgoing: Sequence[TransitionDefinition],
        loop_transition_execution: GraphNodeTransitionExecution | None = None,
    ) -> CompletedNodeDecision:
        loop_transition: TransitionDefinition | None = None
        for t in outgoing:
            if t.edge_type == EdgeType.LOOP:
                loop_transition = t
                break

        if loop_transition is None or loop_transition.target_node_execution_id is None:
            return AdvanceOrFinishSignal()

        if loop_transition_execution is None:
            return AdvanceOrFinishSignal()

        if loop_transition_execution.current_iteration.value >= (
            loop_transition_execution.max_iterations.value or 0
        ):
            return AdvanceOrFinishSignal()

        return LoopDecision(
            target_node_execution_id=loop_transition.target_node_execution_id,
        )

    @staticmethod
    def decide_after_failure(
        *,
        outgoing_transitions: Sequence[TransitionDefinition],
        reason: str,
        policy: GraphNodeExecutionPolicy,
    ) -> FailedNodeDecision:
        """Decide what to do after a node fails.

        Args:
            outgoing_transitions: Transition definitions outgoing from the failed node.
            reason: The failure reason.
            policy: Failure policy to consult if no ERROR_HANDLER transition exists.
        """
        for t in outgoing_transitions:
            if t.edge_type == EdgeType.ERROR_HANDLER and t.target_node_execution_id is not None:
                return ErrorHandlerDecision(target_node_execution_id=t.target_node_execution_id)

        policy_decision = policy.decide_after_failure(None, None, reason)  # type: ignore[arg-type]
        if isinstance(policy_decision, ContinueDecision):
            return AdvanceOrFinishSignal()

        abort_reason = (
            policy_decision.reason if isinstance(policy_decision, PolicyAbortDecision) else reason
        )
        return AbortWorkflowDecision(reason=abort_reason)
