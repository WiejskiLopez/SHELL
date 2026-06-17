"""GraphRepository port — persistence boundary for the Graph aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.entities.graph import Graph
    from shell.domain.value_objects.ids import GraphId, TaskExecutionId


class GraphRepository(Protocol):
    async def get_by_id(self, graph_id: GraphId) -> Graph | None: ...
    async def get_by_task_execution_id(self, task_execution_id: TaskExecutionId) -> Graph | None: ...
    async def save(self, graph: Graph) -> None: ...
