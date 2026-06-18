from __future__ import annotations

from enum import StrEnum


class EnvelopeStage(StrEnum):
    DRAFT = "draft"
    SENT = "sent"
    RECEIVED = "received"
    PROCESSING = "processing"
    DONE = "done"
    ARCHIVED = "archived"
