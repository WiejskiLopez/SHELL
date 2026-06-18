from shell.domain.exceptions._base import DomainError


class InvalidEnvelopeTransition(DomainError):
    """Raised when envelope status/stage transition is forbidden."""
