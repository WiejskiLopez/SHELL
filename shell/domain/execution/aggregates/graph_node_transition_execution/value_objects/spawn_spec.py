from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from shell.domain.execution.value_objects.node_role import NodeRole
from shell.domain.platform.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class SpawnSpec(ValueObject):
    goal: str
    skills: tuple[dict[str, Any], ...]
    target_role: NodeRole | None = None
