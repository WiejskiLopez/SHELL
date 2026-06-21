"""Envelope aggregate with embedded EnvelopeEvents."""

from __future__ import annotations

from shell.domain.execution.aggregates.envelope.entities.envelope_event import EnvelopeEvent
from shell.domain.execution.aggregates.envelope.envelope import _STATUS_TRANSITIONS, Envelope

__all__ = [
    "Envelope",
    "EnvelopeEvent",
    "_STATUS_TRANSITIONS",
]
