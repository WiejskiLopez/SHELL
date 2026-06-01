"""envelope_status.py
EnvelopeStatus — semantic state of an envelope from the workflow's perspective.
"""

from __future__ import annotations

from enum import Enum


class EnvelopeStatus(str, Enum):
    REQUESTED = "REQUESTED"
    DISPATCHED = "DISPATCHED"
    RESPONDED = "RESPONDED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    WAITING = "WAITING"
