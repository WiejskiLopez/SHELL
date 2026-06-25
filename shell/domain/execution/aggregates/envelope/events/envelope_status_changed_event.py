from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.envelope.value_objects.envelope_id import EnvelopeId
from shell.domain.platform.events.domain_event import DomainEvent
from shell.domain.platform.value_objects.envelope_status.envelope_status import EnvelopeStatus


@dataclass(frozen=True, slots=True)
class EnvelopeStatusChangedEvent(DomainEvent):
    envelope_id: EnvelopeId
    previous_status: EnvelopeStatus
    new_status: EnvelopeStatus

    @classmethod
    def now(
        cls, envelope_id: EnvelopeId, previous_status: EnvelopeStatus, new_status: EnvelopeStatus, now: datetime
    ) -> EnvelopeStatusChangedEvent:
        return cls(occurred_at=now, envelope_id=envelope_id, previous_status=previous_status, new_status=new_status)

    @classmethod
    def from_payload(cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            envelope_id=EnvelopeId(payload.get("envelope_id")),
            previous_status=EnvelopeStatus(payload.get("previous_status")),
            new_status=EnvelopeStatus(payload.get("new_status")),
        )
