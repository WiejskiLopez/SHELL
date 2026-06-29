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
from shell.domain.platform.value_objects.exists_result import ExistsResult
from shell.domain.platform.value_objects.state_direction import StateDirection
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
        id_value = id_.value if hasattr(id_, "value") else id_
        model = await self._session.get(GraphNodeExecutionStateModel, id_value)
        if model is None:
            return None
        return self._model_to_entity(model)

    async def list_by_graph_node_execution_id(
        self, graph_node_execution_id: GraphNodeExecutionId
    ) -> list[GraphNodeExecutionState]:
        query = select(GraphNodeExecutionStateModel).where(
            GraphNodeExecutionStateModel.graph_node_execution_id == graph_node_execution_id.value
        )
        rows = (await self._session.execute(query)).scalars().all()
        return [self._model_to_entity(r) for r in rows if r]

    async def list_by_graph_node_execution_and_direction(
        self, graph_node_execution_id: GraphNodeExecutionId, direction: StateDirection
    ) -> list[GraphNodeExecutionState]:
        query = (
            select(GraphNodeExecutionStateModel)
            .where(
                GraphNodeExecutionStateModel.graph_node_execution_id == graph_node_execution_id.value,
                GraphNodeExecutionStateModel.direction == direction.value,
            )
        )
        rows = (await self._session.execute(query)).scalars().all()
        return [self._model_to_entity(r) for r in rows if r]

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
        id_value = id_.value if hasattr(id_, "value") else id_
        model = await self._session.get(GraphNodeExecutionStateModel, id_value)
        if model is not None:
            await self._session.delete(model)

    async def exists(self, id_: object) -> ExistsResult:
        id_value = id_.value if hasattr(id_, "value") else id_
        model = await self._session.get(GraphNodeExecutionStateModel, id_value)
        return ExistsResult(model is not None)

    @staticmethod
    def _model_to_entity(model: GraphNodeExecutionStateModel) -> GraphNodeExecutionState:
        from shell.domain.execution.aggregates.graph_node_execution_state.value_objects.graph_node_execution_state_id import (
            GraphNodeExecutionStateId,
        )
        from shell.domain.platform.value_objects.created_at import CreatedAt
        from shell.domain.platform.value_objects.state_data import StateData

        return GraphNodeExecutionState(  # type: ignore[call-arg]
            id=GraphNodeExecutionStateId(model.id),
            graph_node_execution_id=GraphNodeExecutionId(model.graph_node_execution_id),
            direction=StateDirection(model.direction),
            state_data=StateData(dict(model.state_data or {})),
            is_current=model.is_current,
            created_at=CreatedAt.from_datetime(model.created_at),
        )
