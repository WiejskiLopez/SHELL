from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.execution.aggregates.envelope import Envelope
from shell.domain.execution.aggregates.envelope.services.envelope_lifecycle_service import (
    EnvelopeLifecycleService,
)
from shell.domain.execution.value_objects.ids import EnvelopeId, GraphNodeExecutionId, WorkflowId
from shell.domain.platform.value_objects.envelope_status import EnvelopeStatus

_NOW = datetime(2026, 6, 1, 12, 0, 0, tzinfo=UTC)


def _make_envelope(step: int = 0, status: EnvelopeStatus = EnvelopeStatus.ACTIVE) -> Envelope:
    e = Envelope.new(
        id_=EnvelopeId.generate(),
        workflow_id=WorkflowId.generate(),
        sender_graph_node_execution_id=GraphNodeExecutionId("s"),
        receiver_graph_node_execution_id=GraphNodeExecutionId("r"),
        source_role="a",
        target_role="b",
        step=step,
        now=_NOW,
    )
    if status != EnvelopeStatus.PENDING:
        e.transition_status(status, now=_NOW)
    return e


class TestShouldExpire:
    def test_max_step_zero_never_expires(self) -> None:
        e = _make_envelope(step=100)
        assert not EnvelopeLifecycleService.should_expire(e, 0)

    def test_max_step_negative_never_expires(self) -> None:
        e = _make_envelope(step=5)
        assert not EnvelopeLifecycleService.should_expire(e, -1)

    def test_step_equals_max_step_returns_true(self) -> None:
        e = _make_envelope(step=5)
        assert EnvelopeLifecycleService.should_expire(e, 5)

    def test_step_exceeds_max_step_returns_true(self) -> None:
        e = _make_envelope(step=10)
        assert EnvelopeLifecycleService.should_expire(e, 5)

    def test_step_below_max_step_returns_false(self) -> None:
        e = _make_envelope(step=3)
        assert not EnvelopeLifecycleService.should_expire(e, 5)


class TestAdvance:
    def test_advance_dead_when_step_exceeds_max(self) -> None:
        e = _make_envelope(step=5, status=EnvelopeStatus.ACTIVE)
        result = EnvelopeLifecycleService.advance(e, 3)
        assert result == EnvelopeStatus.DEAD

    def test_advance_keeps_status_when_below_max(self) -> None:
        e = _make_envelope(step=2, status=EnvelopeStatus.ACTIVE)
        result = EnvelopeLifecycleService.advance(e, 5)
        assert result == EnvelopeStatus.ACTIVE

    def test_advance_max_step_zero_keeps_status(self) -> None:
        e = _make_envelope(step=99, status=EnvelopeStatus.ACTIVE)
        result = EnvelopeLifecycleService.advance(e, 0)
        assert result == EnvelopeStatus.ACTIVE

    def test_advance_pending_stays_pending_when_not_expired(self) -> None:
        e = _make_envelope(step=0, status=EnvelopeStatus.PENDING)
        result = EnvelopeLifecycleService.advance(e, 10)
        assert result == EnvelopeStatus.PENDING
