"""Platform enum describing the explicit inbox delivery lifecycle."""

from __future__ import annotations

from enum import StrEnum

from shell.platform.domain.base.value_object import ValueObject


class InboxStatus(ValueObject, StrEnum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    RETRY = "RETRY"
    DEAD_LETTER = "DEAD_LETTER"
    LEGACY_REVIEW = "LEGACY_REVIEW"
