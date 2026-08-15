from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.ingestion_service.domain.ingestion.aggregates.ingestion.value_objects.ingestion_id import (
        IngestionId,
    )
    from shell.platform.domain.value_objects.occurred_at import OccurredAt


@dataclass(frozen=True, slots=True)
class IngestionChangedEvent(DomainEvent):
    ingestion_id: IngestionId

    @classmethod
    def now(cls, ingestion_id: IngestionId, now: OccurredAt) -> IngestionChangedEvent:
        return cls(occurred_at=now, ingestion_id=ingestion_id)
