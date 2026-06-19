from __future__ import annotations

from enum import StrEnum


class ConditionLanguage(StrEnum):
    PYTHON = "python"
    JSONPATH = "jsonpath"
    SIMPLE = "simple"
