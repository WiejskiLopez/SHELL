from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from shell.platform.domain.value_objects.aggregate_id import AggregateId
from shell.platform.domain.value_objects.event_id import EventId

if TYPE_CHECKING:
    from shell.platform.domain.value_objects.occurred_at import OccurredAt


@dataclass(frozen=True, slots=True, kw_only=True)
class DomainEvent:
    event_id: EventId = field(default_factory=EventId.generate)
    aggregate_id: AggregateId = field(default_factory=AggregateId.generate)
    occurred_at: OccurredAt
