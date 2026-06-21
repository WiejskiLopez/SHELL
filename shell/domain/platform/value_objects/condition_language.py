from __future__ import annotations

from enum import StrEnum

from shell.domain.platform.base.value_object import ValueObject


class ConditionLanguage(ValueObject, StrEnum):
    PYTHON = "python"
    JSONPATH = "jsonpath"
    SIMPLE = "simple"
