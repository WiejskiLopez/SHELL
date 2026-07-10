"""AggregateDeletedEvent — emitted when an aggregate is soft-deleted."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events.domain_event import DomainEvent
from shell.platform.domain.value_objects.created_at import CreatedAt

if TYPE_CHECKING:
    from shell.platform.domain.value_objects.deleted_at import DeletedAt


@dataclass(frozen=True, slots=True)
class AggregateDeletedEvent(DomainEvent):
    deleted_at: DeletedAt

    @classmethod
    def now(cls, deleted_at: DeletedAt) -> AggregateDeletedEvent:
        return cls(
            occurred_at=CreatedAt.from_datetime(deleted_at.value),
            deleted_at=deleted_at,
        )
