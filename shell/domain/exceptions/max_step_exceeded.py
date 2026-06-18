from shell.domain.exceptions._base import DomainError


class MaxStepExceeded(DomainError):
    """Raised when envelope step >= max_step TTL."""
