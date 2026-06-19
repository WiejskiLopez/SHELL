from __future__ import annotations

from shell.domain.platform.exceptions._base import DomainError


class MaxStepExceeded(DomainError):
    """Raised when envelope step >= max_step TTL."""
