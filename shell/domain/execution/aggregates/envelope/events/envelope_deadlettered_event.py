from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.envelope.envelope_id import EnvelopeId
from shell.domain.execution.aggregates.workflow.workflow_id import WorkflowId
from shell.domain.platform.events import DomainEvent


@dataclass(frozen=True, slots=True)
class EnvelopeDeadletteredEvent(DomainEvent):
    envelope_id: EnvelopeId
    workflow_id: WorkflowId
    reason: str

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            envelope_id=EnvelopeId(payload["envelope_id"]),
            workflow_id=WorkflowId(payload["workflow_id"]),
            reason=payload["reason"],
        )

    @classmethod
    def now(
        cls, envelope_id: EnvelopeId, workflow_id: WorkflowId, reason: str, now: datetime
    ) -> EnvelopeDeadletteredEvent:
        return cls(
            occurred_at=now,
            envelope_id=envelope_id,
            workflow_id=workflow_id,
            reason=reason,
        )
