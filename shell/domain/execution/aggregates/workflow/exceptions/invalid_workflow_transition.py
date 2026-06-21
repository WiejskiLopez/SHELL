from __future__ import annotations

from shell.domain.platform.exceptions._base import DomainError


class InvalidWorkflowTransition(DomainError):
    """Raised when a state-machine transition on Workflow is forbidden."""
