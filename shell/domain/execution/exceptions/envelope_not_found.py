from __future__ import annotations

from shell.domain.platform.exceptions._base import DomainError


class EnvelopeNotFound(DomainError):
    def __init__(self, envelope_id: str) -> None:
        super().__init__(f"Envelope not found: {envelope_id!r}")
