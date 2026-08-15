"""AggregateDeletedEvent — emitted when an aggregate is soft-deleted."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events.domain_event import DomainEvent

if TYPE_CHECKING:
    from shell.platform.domain.value_objects.occurred_at import OccurredAt


@dataclass(frozen=True, slots=True)
class AggregateDeletedEvent(DomainEvent):
    @classmethod
    def now(cls, deleted_at: OccurredAt) -> AggregateDeletedEvent:
        return cls(occurred_at=deleted_at)
