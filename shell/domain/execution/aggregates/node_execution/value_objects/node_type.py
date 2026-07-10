from __future__ import annotations

from dataclasses import dataclass

from shell.platform.domain.base import ValueObject


@dataclass(frozen=True, slots=True)
class NodeType(ValueObject):
    value: str
