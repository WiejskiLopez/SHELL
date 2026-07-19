from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from shell.platform.domain.base.value_object import ValueObject
from shell.platform.domain.value_objects.timestamp import Timestamp


@dataclass(frozen=True, slots=True)
class OccurredAt(ValueObject):
    value: datetime

    def __post_init__(self) -> None:
        if self.value.tzinfo is None:
            raise ValueError("OccurredAt must be timezone-aware (UTC)")

    def __str__(self) -> str:
        return self.value.isoformat()

    @classmethod
    def now(cls) -> OccurredAt:
        return cls(datetime.now(tz=UTC))

    @classmethod
    def from_datetime(cls, dt: datetime) -> OccurredAt:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return cls(dt)

    def to_timestamp(self) -> Timestamp:
        return Timestamp(self.value)
