"""Unit tests for Envelope entity."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from shell.domain.execution.entities.envelope import Envelope
from shell.domain.exceptions import InvalidEnvelopeTransition
from shell.domain.platform.value_objects.envelope_status import EnvelopeStage, EnvelopeStatus
from shell.domain.platform.value_objects.ids import (
    EnvelopeId,
    GraphNodeExecutionId,
    WorkflowId,
)

_NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)


class TestEnvelope:
    def _make_envelope(self) -> Envelope:
        return Envelope.new(
            id_=EnvelopeId.generate(),
            workflow_id=WorkflowId.generate(),
            sender_graph_node_execution_id=GraphNodeExecutionId("sender"),
            receiver_graph_node_execution_id=GraphNodeExecutionId("receiver"),
            source_role="agent",
            target_role="router",
            now=_NOW,
        )

    def test_new_is_pending_draft(self) -> None:
        e = self._make_envelope()
        assert e.status == EnvelopeStatus.PENDING
        assert e.stage == EnvelopeStage.DRAFT

    def test_valid_transition_pending_to_active(self) -> None:
        e = self._make_envelope()
        e.transition_status(EnvelopeStatus.ACTIVE, now=_NOW)
        assert e.status == EnvelopeStatus.ACTIVE
        assert len(e.events) == 1

    def test_invalid_transition_raises(self) -> None:
        e = self._make_envelope()
        with pytest.raises(InvalidEnvelopeTransition):
            e.transition_status(EnvelopeStatus.DELIVERED, now=_NOW)

    def test_dead_is_terminal(self) -> None:
        e = self._make_envelope()
        e.transition_status(EnvelopeStatus.DEAD, now=_NOW)
        with pytest.raises(InvalidEnvelopeTransition):
            e.transition_status(EnvelopeStatus.PENDING, now=_NOW)
