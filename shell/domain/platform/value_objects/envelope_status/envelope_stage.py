from __future__ import annotations

from enum import StrEnum

from shell.domain.platform.base.value_object import ValueObject


class EnvelopeStage(ValueObject, StrEnum):
    DRAFT = "draft"
    SENT = "sent"
    RECEIVED = "received"
    PROCESSING = "processing"
    DONE = "done"
    ARCHIVED = "archived"
