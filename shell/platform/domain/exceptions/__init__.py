"""Platform exceptions — base class for all domain errors."""

from __future__ import annotations

from shell.platform.domain.exceptions.concurrent_modification_error import (
    ConcurrentModificationError,
)
from shell.platform.domain.exceptions.domain_error import DomainError

__all__ = [
    "ConcurrentModificationError",
    "DomainError",
]
