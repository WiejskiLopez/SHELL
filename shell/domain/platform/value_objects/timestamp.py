"""Timestamp value object — UTC datetime wrapper."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from shell.domain.platform.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class Timestamp(ValueObject):
    value: datetime

    def __post_init__(self) -> None:
        if self.value.tzinfo is None:
            raise ValueError("Timestamp must be timezone-aware (UTC)")

    def __str__(self) -> str:
        return self.value.isoformat()

    @classmethod
    def now(cls) -> Timestamp:
        return cls(datetime.now(tz=UTC))

    @classmethod
    def from_datetime(cls, dt: datetime) -> Timestamp:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return cls(dt)
