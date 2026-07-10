from __future__ import annotations

from enum import StrEnum

from shell.platform.domain.base.value_object import ValueObject


class NodeRole(ValueObject, StrEnum):
    PLANNER = "PLANNER"
    AGENT = "AGENT"
    TOOL = "TOOL"
    VERIFIER = "VERIFIER"
