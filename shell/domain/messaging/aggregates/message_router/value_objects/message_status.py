from __future__ import annotations

from enum import StrEnum

from shell.platform.domain.base.value_object import ValueObject


class MessageStatus(ValueObject, StrEnum):
    CREATED = "created"
    RECEIVED = "received"
