from __future__ import annotations

from shell.platform.domain.exceptions.domain_error import DomainError


class InvalidNodeMode(DomainError):
    """Raised when an unknown node mode is encountered."""
