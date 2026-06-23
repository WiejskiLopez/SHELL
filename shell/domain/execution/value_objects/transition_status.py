from __future__ import annotations

from enum import StrEnum

from shell.domain.platform.base.value_object import ValueObject


class TransitionStatus(ValueObject, StrEnum):
    EVALUATED = "EVALUATED"
    TAKEN = "TAKEN"
    SKIPPED = "SKIPPED"
