from __future__ import annotations

from shell.platform.domain.exceptions.domain_error import DomainError


class InvalidWorkflowTransition(DomainError):
    """Raised when an invalid workflow state transition is attempted."""

    def __init__(self, from_status: str, to_status: str) -> None:
        super().__init__(f"Invalid workflow transition from {from_status!r} to {to_status!r}")
