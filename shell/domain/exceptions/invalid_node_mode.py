from __future__ import annotations

from shell.domain.exceptions._base import DomainError


class InvalidNodeMode(DomainError):
    """Raised when an unknown node mode is encountered."""
