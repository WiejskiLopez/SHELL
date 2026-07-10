from __future__ import annotations

from enum import StrEnum

from shell.platform.domain.base.value_object import ValueObject


class SystemRole(ValueObject, StrEnum):
    PLANNER = "PLANNER"
    DEVELOPER = "DEVELOPER"
    TESTER = "TESTER"
