from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime  # noqa: TC003 — Mapped[datetime] wymaga datetime w runtime


@dataclass
class OutboxRecord:
    id: str
    event_type: str
    occurred_at: datetime
    payload: dict  # type: ignore[type-arg]
    published_at: datetime | None = None

    @property
    def is_published(self) -> bool:
        return self.published_at is not None
