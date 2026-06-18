from __future__ import annotations

from enum import StrEnum


class EnvelopeStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    DELIVERED = "delivered"
    FAILED = "failed"
    DEAD = "dead"
