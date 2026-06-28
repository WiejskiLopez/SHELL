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
from shell.domain.execution.value_objects.state_direction import StateDirection
from shell.infrastructure.execution.persistence.sql.models.graph_node_execution_state_aggregate import (
    GraphNodeExecutionStateModel,
)
from sqlalchemy import select

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

    async def list_by_graph_node_execution_and_direction(
        self, graph_node_execution_id: GraphNodeExecutionId, direction: StateDirection
    ) -> list[GraphNodeExecutionState]:
        ...

    async def save(self, state: GraphNodeExecutionState) -> None:
        model = await self._session.get(
            GraphNodeExecutionStateModel, state.id.value
        )
        if model is None:
            model = GraphNodeExecutionStateModel(
                id=state.id.value,
                graph_node_execution_id=state.graph_node_execution_id.value,
                direction=state.direction.value,
                state_data=state.state_data.to_dict(),
                is_current=True,
                created_at=state.created_at.value,
            )
            self._session.add(model)
        else:
            model.state_data = state.state_data.to_dict()

    async def delete(self, id_: object) -> None:
        ...

    async def exists(self, id_: object) -> bool:
        ...
