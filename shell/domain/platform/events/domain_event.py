from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True, kw_only=True)
class DomainEvent:
    event_id: str = ""
    aggregate_id: str = ""
    aggregate_type: str = ""
    occurred_at: datetime
    schema_version: int = 1

    def __post_init__(self) -> None:
        if not self.event_id:
            import uuid
            object.__setattr__(self, "event_id", str(uuid.uuid4()))

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        raise NotImplementedError
