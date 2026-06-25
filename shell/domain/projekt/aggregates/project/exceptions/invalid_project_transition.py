from __future__ import annotations

from shell.domain.platform.exceptions.domain_error import DomainError


class InvalidProjectTransition(DomainError):
    """Raised when a state-machine transition on Project is forbidden."""
