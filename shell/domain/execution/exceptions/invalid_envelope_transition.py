from __future__ import annotations

from shell.domain.platform.exceptions._base import DomainError


class InvalidEnvelopeTransition(DomainError):
    """Raised when envelope status/stage transition is forbidden."""
