"""Unit tests for ``NodeExecutionPolicy`` strategy.

The default ``FailFastNodeExecutionPolicy`` always returns ``AbortDecision`` on failure,
preserving the legacy "any failure aborts the whole workflow" semantics.
The protocol allows future strategies (retry, continue-on-error, conditional
branching) to be plugged in without touching the ``NodeExecutionWorker``.
"""

from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.execution.aggregates.workflow import Workflow
from shell.domain.execution.services.node_execution_policy import (
    AbortDecision,
    ContinueDecision,
    FailFastNodeExecutionPolicy,
)
from shell.domain.execution.value_objects.ids import (
    NodeExecutionId,
    WorkflowId,
)


def _workflow() -> Workflow:
    return Workflow.new(
        id_=WorkflowId.generate(),
        now=datetime.now(tz=UTC),
    )


class TestFailFastNodeExecutionPolicy:
    def test_decide_after_failure_returns_abort_decision(self) -> None:
        policy = FailFastNodeExecutionPolicy()
        wf = _workflow()
        decision = policy.decide_after_failure(wf, NodeExecutionId("n1"), reason="boom")
        assert isinstance(decision, AbortDecision)
        assert decision.reason == "boom"

    def test_continue_decision_is_distinguishable_from_abort(self) -> None:
        cont = ContinueDecision()
        abort = AbortDecision(reason="task-id")
        # Type-level discrimination must be sound.
        assert isinstance(cont, ContinueDecision)
        assert isinstance(abort, AbortDecision)
        assert not isinstance(cont, AbortDecision)
        assert not isinstance(abort, ContinueDecision)
