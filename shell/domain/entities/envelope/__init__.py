"""Envelope aggregate with embedded EnvelopeEvents."""
from __future__ import annotations


from shell.domain.entities.envelope.envelope import Envelope, _STATUS_TRANSITIONS
from shell.domain.entities.envelope.envelope_event import EnvelopeEvent

__all__ = [
    "Envelope",
    "EnvelopeEvent",
    "_STATUS_TRANSITIONS",
]
