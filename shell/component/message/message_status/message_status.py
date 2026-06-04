from __future__ import annotations

from enum import Enum


class MessageStatus(str, Enum):
    CREATED = "created"
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
