"""Task aggregate root with embedded Graph and GraphNodes."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from shell_ddd.domain.entities.graph_node import GraphNode

if TYPE_CHECKING:
    from shell_ddd.domain.value_objects.ids import GraphId, TaskId


@dataclass(slots=True)
class Graph:
    """Graph embedded in a Task aggregate."""

    id: GraphId
    task_id: TaskId
    raw_dict: dict[str, object]
    nodes: list[GraphNode] = field(default_factory=list)
