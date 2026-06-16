"""Node entity — lightweight model of a running node instance."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.domain.value_objects.ids import NodeId
    from shell.domain.value_objects.mode import Mode


@dataclass(slots=True)
class Node:
    """Represents a running node instance (not a graph definition node)."""

    id: NodeId
    mode: Mode
    role: str
    node_type: str
    workspace_path: str  # opaque str, resolved by NodeWorkspace in infrastructure
