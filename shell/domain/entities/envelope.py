"""Envelope aggregate with embedded EnvelopeEvents."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from shell.domain.exceptions import InvalidEnvelopeTransition
from shell.domain.value_objects.envelope_status import EnvelopeStage, EnvelopeStatus

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.value_objects.ids import EnvelopeEventId, EnvelopeId, GraphNodeExecutionId, WorkflowId


@dataclass(slots=True)
class EnvelopeEvent:
    id: EnvelopeEventId
    kind: str
    payload: dict[str, object]
    created_at: datetime


# Allowed status transitions
_STATUS_TRANSITIONS: dict[EnvelopeStatus, set[EnvelopeStatus]] = {
    EnvelopeStatus.PENDING: {EnvelopeStatus.ACTIVE, EnvelopeStatus.DEAD},
    EnvelopeStatus.ACTIVE: {EnvelopeStatus.DELIVERED, EnvelopeStatus.FAILED},
    EnvelopeStatus.DELIVERED: set(),
    EnvelopeStatus.FAILED: {EnvelopeStatus.PENDING, EnvelopeStatus.DEAD},
    EnvelopeStatus.DEAD: set(),
}


@dataclass(slots=True)
class Envelope:
    """Envelope aggregate root."""

    id: EnvelopeId
    workflow_id: WorkflowId
    parent_id: EnvelopeId | None
    correlation_id: str
    sender_graph_node_execution_id: GraphNodeExecutionId
    receiver_graph_node_execution_id: GraphNodeExecutionId
    source_role: str
    target_role: str
    sequence_id: int
    step: int
    status: EnvelopeStatus
    stage: EnvelopeStage
    payload: dict[str, object]
    artifact_uri: str
    archive_uri: str
    created_at: datetime
    updated_at: datetime
    events: list[EnvelopeEvent] = field(default_factory=list)

    @classmethod
    def new(
        cls,
        *,
        id_: EnvelopeId,
        workflow_id: WorkflowId,
        sender_graph_node_execution_id: GraphNodeExecutionId,
        receiver_graph_node_execution_id: GraphNodeExecutionId,
        source_role: str,
        target_role: str,
        correlation_id: str = "",
        parent_id: EnvelopeId | None = None,
        sequence_id: int = 0,
        step: int = 0,
        payload: dict[str, object] | None = None,
        now: datetime,
    ) -> Envelope:
        return cls(
            id=id_,
            workflow_id=workflow_id,
            parent_id=parent_id,
            correlation_id=correlation_id or str(id_),
            sender_graph_node_execution_id=sender_graph_node_execution_id,
            receiver_graph_node_execution_id=receiver_graph_node_execution_id,
            source_role=source_role,
            target_role=target_role,
            sequence_id=sequence_id,
            step=step,
            status=EnvelopeStatus.PENDING,
            stage=EnvelopeStage.DRAFT,
            payload=payload or {},
            artifact_uri="",
            archive_uri="",
            created_at=now,
            updated_at=now,
        )

    def transition_status(self, new_status: EnvelopeStatus, now: datetime) -> None:
        allowed = _STATUS_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise InvalidEnvelopeTransition(
                f"Cannot transition envelope {self.id.value!r} "
                f"from {self.status.value!r} to {new_status.value!r}"
            )
        self.status = new_status
        self.updated_at = now
        from shell.domain.value_objects.ids import EnvelopeEventId

        self.events.append(
            EnvelopeEvent(
                id=EnvelopeEventId.generate(),
                kind="status_changed",
                payload={"status": new_status.value},
                created_at=now,
            )
        )

    def transition_stage(self, new_stage: EnvelopeStage, now: datetime) -> None:
        self.stage = new_stage
        self.updated_at = now
