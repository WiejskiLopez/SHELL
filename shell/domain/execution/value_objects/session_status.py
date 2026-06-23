from __future__ import annotations

from enum import StrEnum

from shell.domain.platform.base.value_object import ValueObject


class SessionStatus(ValueObject, StrEnum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
