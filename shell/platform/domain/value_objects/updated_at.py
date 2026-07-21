"""UpdatedAt value object — znacznik czasu ostatniej modyfikacji encji/agregatu."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from shell.platform.domain.base.value_object import ValueObject
from shell.platform.domain.value_objects.timestamp import Timestamp


@dataclass(frozen=True, slots=True)
class UpdatedAt(ValueObject):
    value: datetime | None

    def __post_init__(self) -> None:
        if self.value is not None and self.value.tzinfo is None:
            raise ValueError("UpdatedAt must be timezone-aware (UTC)")

    def __str__(self) -> str:
        return self.value.isoformat() if self.value is not None else ""

    @classmethod
    def none(cls) -> UpdatedAt:
        return cls(value=None)

    @classmethod
    def now(cls) -> UpdatedAt:
        return cls(datetime.now(tz=UTC))

    @classmethod
    def from_datetime(cls, dt: datetime | None) -> UpdatedAt:
        if dt is not None and dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return cls(dt)

    def to_timestamp(self) -> Timestamp | None:
        return Timestamp(self.value) if self.value is not None else None


NONE_UPDATED_AT: UpdatedAt = UpdatedAt(value=None)
