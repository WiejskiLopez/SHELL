from __future__ import annotations

from enum import StrEnum

from shell.domain.platform.base.value_object import ValueObject


class NodeRole(ValueObject, StrEnum):
    PLANNER = "PLANNER"
    AGENT = "AGENT"
    TOOLS = "TOOLS"
    VERIFIER = "VERIFIER"
