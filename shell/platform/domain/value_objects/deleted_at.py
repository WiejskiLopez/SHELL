"""DeletedAt value object — znacznik czasu miękkiego usunięcia agregatu."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from shell.platform.domain.base.value_object import ValueObject
from shell.platform.domain.exceptions.domain_error import DomainError
from shell.platform.domain.value_objects.timestamp import Timestamp


@dataclass(frozen=True, slots=True)
class DeletedAt(ValueObject):
    value: datetime | None = None

    def __post_init__(self) -> None:
        if self.value is not None and self.value.tzinfo is None:
            raise DomainError("DeletedAt must be timezone-aware (UTC)")

    @classmethod
    def none(cls) -> DeletedAt:
        return cls(value=None)

    @classmethod
    def now(cls) -> DeletedAt:
        return cls(datetime.now(tz=UTC))

    @classmethod
    def from_datetime(cls, dt: datetime | None) -> DeletedAt:
        if dt is not None and dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return cls(dt)

    def to_timestamp(self) -> Timestamp | None:
        return Timestamp(self.value) if self.value is not None else None


NONE_DELETED_AT: DeletedAt = DeletedAt(value=None)
