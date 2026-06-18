from shell.domain.exceptions._base import DomainError


class InvalidWorkflowTransition(DomainError):
    """Raised when a state-machine transition on Workflow is forbidden."""
