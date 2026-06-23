from __future__ import annotations

from enum import StrEnum

from shell.domain.platform.base.value_object import ValueObject


class ProjectStatus(ValueObject, StrEnum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
