from __future__ import annotations

from shell.platform.domain.exceptions.domain_error import DomainError


class RoleNotResolvable(DomainError):
    """Raised when no graph node satisfies the requested role."""
