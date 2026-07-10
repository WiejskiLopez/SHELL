from __future__ import annotations

from enum import StrEnum

from shell.platform.domain.base.value_object import ValueObject


class StateDirection(ValueObject, StrEnum):
    IN = "IN"
    OUT = "OUT"
