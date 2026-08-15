"""Hash value object — SHA-256 hex digest."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from shell.platform.domain.base.value_object import ValueObject
from shell.platform.domain.exceptions.domain_error import DomainError


@dataclass(frozen=True, slots=True)
class Hash(ValueObject):
    value: str  # hex digest

    def __post_init__(self) -> None:
        if len(self.value) != 64:
            raise DomainError(f"Hash must be 64 hex chars (SHA-256), got {len(self.value)}")
        try:
            int(self.value, 16)
        except ValueError:
            raise DomainError("Hash must be a valid hex string") from None

    def __str__(self) -> str:
        return self.value

    @classmethod
    def of(cls, data: str | bytes) -> Hash:
        raw = data.encode() if isinstance(data, str) else data
        return cls(hashlib.sha256(raw).hexdigest())
