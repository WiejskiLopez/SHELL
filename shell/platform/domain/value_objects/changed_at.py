"""ChangedAt value object - znacznik czasu ostatniej modyfikacji encji/agregatu."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from shell.platform.domain.base.value_object import ValueObject
from shell.platform.domain.exceptions.domain_error import DomainError
from shell.platform.domain.value_objects.timestamp import Timestamp


@dataclass(frozen=True, slots=True)
class ChangedAt(ValueObject):
    value: datetime | None

    def __post_init__(self) -> None:
        if self.value is not None and self.value.tzinfo is None:
            raise DomainError("ChangedAt must be timezone-aware (UTC)")

    @classmethod
    def none(cls) -> ChangedAt:
        return cls(value=None)

    @classmethod
    def now(cls) -> ChangedAt:
        return cls(datetime.now(tz=UTC))

    @classmethod
    def from_datetime(cls, dt: datetime | None) -> ChangedAt:
        if dt is not None and dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return cls(dt)

    def to_timestamp(self) -> Timestamp | None:
        return Timestamp(self.value) if self.value is not None else None


NONE_CHANGED_AT: ChangedAt = ChangedAt(value=None)
