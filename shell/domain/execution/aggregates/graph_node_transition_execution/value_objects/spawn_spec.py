from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from shell.domain.execution.value_objects.node_role import NodeRole


@dataclass(frozen=True, slots=True)
class SpawnSpec:
    goal: str
    skills: tuple[dict[str, Any], ...]
    target_role: NodeRole | None = None
