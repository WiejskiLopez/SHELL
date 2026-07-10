"""AggregateRestoredEvent — emitted when a soft-deleted aggregate is restored."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events.domain_event import DomainEvent

if TYPE_CHECKING:
    from shell.platform.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class AggregateRestoredEvent(DomainEvent):
    @classmethod
    def now(cls, now: CreatedAt) -> AggregateRestoredEvent:
        return cls(occurred_at=now)
