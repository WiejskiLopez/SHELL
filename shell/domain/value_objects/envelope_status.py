"""EnvelopeStatus and EnvelopeStage value objects."""

from __future__ import annotations

from enum import StrEnum


class EnvelopeStatus(StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    DELIVERED = "delivered"
    FAILED = "failed"
    DEAD = "dead"


class EnvelopeStage(StrEnum):
    DRAFT = "draft"
    SENT = "sent"
    RECEIVED = "received"
    PROCESSING = "processing"
    DONE = "done"
    ARCHIVED = "archived"
