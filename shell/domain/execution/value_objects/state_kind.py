from __future__ import annotations

from enum import StrEnum

from shell.domain.platform.base.value_object import ValueObject


class StateKind(ValueObject, StrEnum):
    INPUT = "input"
    OUTPUT = "output"
