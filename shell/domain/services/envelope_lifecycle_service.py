"""EnvelopeLifecycleService — pure domain TTL/expiry logic."""
from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.value_objects.envelope_status import EnvelopeStatus

if TYPE_CHECKING:
    from shell.domain.entities.envelope import Envelope


class EnvelopeLifecycleService:
    """Determines whether an envelope should be expired based on step count."""

    @staticmethod
    def should_expire(envelope: Envelope, max_step: int) -> bool:
        """Return True if envelope has exceeded the max_step TTL."""
        if max_step <= 0:
            return False
        return envelope.step >= max_step

    @staticmethod
    def advance(envelope: Envelope, max_step: int) -> EnvelopeStatus:
        """Return the new status after considering TTL.

        - If step >= max_step → DEAD
        - Else keep current status.
        """
        if EnvelopeLifecycleService.should_expire(envelope, max_step):
            return EnvelopeStatus.DEAD
        return envelope.status
