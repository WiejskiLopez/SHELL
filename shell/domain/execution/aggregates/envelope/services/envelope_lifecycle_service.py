"""EnvelopeLifecycleService — pure domain TTL/expiry logic."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.platform.value_objects.envelope_status import EnvelopeStatus

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.envelope import Envelope


class EnvelopeLifecycleService:
    """Determines whether an envelope should be expired based on step count."""

    @staticmethod
    def should_expire(envelope: Envelope, max_step: int) -> bool:
        """Return True if envelope has exceeded the max_step TTL."""
        if max_step <= 0:
            return False
        return envelope.step >= max_step

    @staticmethod
    def evaluate_status(envelope: Envelope, max_step: int) -> EnvelopeStatus:
        """Return the status the envelope should transition to based on TTL.

        - If step >= max_step → DEAD
        - Else keep current status.
        """
        if EnvelopeLifecycleService.should_expire(envelope, max_step):
            return EnvelopeStatus.DEAD
        return envelope.status
