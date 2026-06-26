"""CreatedAt value object — znacznik czasu utworzenia encji/agregatu."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from shell.domain.platform.base.value_object import ValueObject
from shell.domain.platform.value_objects.timestamp import Timestamp


@dataclass(frozen=True, slots=True)
class CreatedAt(ValueObject):
    value: datetime

    def __post_init__(self) -> None:
        if self.value.tzinfo is None:
            raise ValueError("CreatedAt must be timezone-aware (UTC)")

    def __str__(self) -> str:
        return self.value.isoformat()

    @classmethod
    def now(cls) -> CreatedAt:
        return cls(datetime.now(tz=UTC))

    def to_timestamp(self) -> Timestamp:
        return Timestamp(self.value)
