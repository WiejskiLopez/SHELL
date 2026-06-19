"""Envelope aggregate with embedded EnvelopeEvents."""
from __future__ import annotations

from shell.domain.execution.entities.envelope.envelope import _STATUS_TRANSITIONS, Envelope
from shell.domain.execution.entities.envelope.envelope_event import EnvelopeEvent

__all__ = [
    "Envelope",
    "EnvelopeEvent",
    "_STATUS_TRANSITIONS",
]
