"""GraphRepository port — persistence boundary for the Graph aggregate."""
from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell_ddd.domain.entities.graph import Graph
    from shell_ddd.domain.value_objects.ids import GraphId, TaskId


class GraphRepository(Protocol):
    async def get_by_id(self, graph_id: GraphId) -> Graph | None: ...
    async def get_by_task_id(self, task_id: TaskId) -> Graph | None: ...
    async def save(self, graph: Graph) -> None: ...
