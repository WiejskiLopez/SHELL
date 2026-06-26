from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
    GraphNodeExecutionId,
)
from shell.domain.execution.aggregates.graph_node_execution_state.graph_node_execution_state import (
    GraphNodeExecutionState,
)
from shell.domain.execution.aggregates.graph_node_execution_state.repositories.graph_node_execution_state_repository import (
    GraphNodeExecutionStateRepository,
)
from shell.domain.execution.value_objects.state_kind import StateKind

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class SqlGraphNodeExecutionStateRepository(GraphNodeExecutionStateRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id_: object) -> GraphNodeExecutionState | None:
        ...

    async def list_by_graph_node_execution_id(
        self, graph_node_execution_id: GraphNodeExecutionId
    ) -> list[GraphNodeExecutionState]:
        ...

    async def list_by_graph_node_execution_and_kind(
        self, graph_node_execution_id: GraphNodeExecutionId, kind: StateKind
    ) -> list[GraphNodeExecutionState]:
        ...

    async def save(self, state: GraphNodeExecutionState) -> None:
        ...

    async def delete(self, id_: object) -> None:
        ...

    async def exists(self, id_: object) -> bool:
        ...
