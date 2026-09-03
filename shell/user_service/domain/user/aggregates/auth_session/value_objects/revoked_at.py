"""Revocation timestamp for an authentication session."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from shell.platform.domain.base.value_object import ValueObject
from shell.platform.domain.exceptions.domain_error import DomainError


@dataclass(frozen=True, slots=True)
class RevokedAt(ValueObject):
    value: datetime | None = None

    def __post_init__(self) -> None:
        if self.value is not None and self.value.tzinfo is None:
            raise DomainError("RevokedAt must be timezone-aware (UTC)")

    @classmethod
    def none(cls) -> RevokedAt:
        return cls(value=None)

    @classmethod
    def now(cls) -> RevokedAt:
        return cls(datetime.now(tz=UTC))

    @classmethod
    def from_datetime(cls, dt: datetime | None) -> RevokedAt:
        if dt is not None and dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return cls(dt)


NONE_REVOKED_AT: RevokedAt = RevokedAt(value=None)
