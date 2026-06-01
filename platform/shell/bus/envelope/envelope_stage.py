"""envelope_stage.py
EnvelopeStage — bus-side stage replacing the old filesystem subdirectories.
"""

from __future__ import annotations

from enum import Enum


class EnvelopeStage(str, Enum):
    ACTIVE = "ACTIVE"
    PENDING = "PENDING"
    HISTORY = "HISTORY"
    DONE = "DONE"
    DEAD = "DEAD"
    IGNORED = "IGNORED"
