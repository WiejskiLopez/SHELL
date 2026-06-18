from shell.domain.exceptions._base import DomainError


class RoleNotResolvable(DomainError):
    """Raised when no graph node satisfies the requested role."""
