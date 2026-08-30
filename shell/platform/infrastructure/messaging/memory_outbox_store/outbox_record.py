from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


@dataclass
class OutboxRecord:
    id: str
    event_type: str
    occurred_at: datetime
    payload: dict[str, object]
    correlation_id: str = ""
    causation_id: str = ""
    published_at: datetime | None = None

    @property
    def is_published(self) -> bool:
        return self.published_at is not None
