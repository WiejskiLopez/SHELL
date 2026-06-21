from __future__ import annotations

from enum import StrEnum

from shell.domain.platform.base.value_object import ValueObject


class EnvelopeStatus(ValueObject, StrEnum):
    PENDING = "pending"
    ACTIVE = "active"
    DELIVERED = "delivered"
    FAILED = "failed"
    DEAD = "dead"
