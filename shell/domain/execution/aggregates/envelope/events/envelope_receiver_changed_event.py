from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.envelope.value_objects.envelope_id import EnvelopeId
from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
    GraphNodeExecutionId,
)
from shell.domain.platform.events.domain_event import DomainEvent


@dataclass(frozen=True, slots=True)
class EnvelopeReceiverChangedEvent(DomainEvent):
    envelope_id: EnvelopeId
    new_receiver_id: GraphNodeExecutionId

    @classmethod
    def now(
        cls, envelope_id: EnvelopeId, new_receiver_id: GraphNodeExecutionId, now: datetime
    ) -> EnvelopeReceiverChangedEvent:
        return cls(occurred_at=now, envelope_id=envelope_id, new_receiver_id=new_receiver_id)

    @classmethod
    def from_payload(cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            envelope_id=EnvelopeId(payload.get("envelope_id")),
            new_receiver_id=GraphNodeExecutionId(payload.get("new_receiver_id")),
        )
