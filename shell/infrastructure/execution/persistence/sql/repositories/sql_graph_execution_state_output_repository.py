from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.domain.execution.aggregates.graph_execution_state.repositories.graph_execution_state_repository import (
    GraphExecutionStateRepository,
)
from shell.domain.platform.value_objects.exists_result import ExistsResult
from shell.domain.platform.value_objects.state_direction import StateDirection
from shell.infrastructure.execution.persistence.sql.mappers import (
    graph_execution_state_output_entity_to_model,
    graph_execution_state_output_model_to_entity,
)
from sqlalchemy import select, update

from ..models.graph_execution_state_output import GraphExecutionStateOutputModel

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution_state.graph_execution_state import (
        GraphExecutionState,
    )
    from sqlalchemy.ext.asyncio import AsyncSession


class SqlGraphExecutionStateRepository(GraphExecutionStateRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_current_by_graph_execution_id_and_direction(
        self, graph_execution_id: GraphExecutionId, direction: StateDirection
    ) -> GraphExecutionState | None:
        query = (
            select(GraphExecutionStateOutputModel)
            .where(
                GraphExecutionStateOutputModel.graph_execution_id == graph_execution_id.value,
                GraphExecutionStateOutputModel.is_current.is_(True),
            )
            .limit(1)
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        return graph_execution_state_output_model_to_entity(row) if row else None

    async def save(self, state: GraphExecutionState) -> None:
        if state.is_current.value:
            await self._session.execute(
                update(GraphExecutionStateOutputModel)
                .where(
                    GraphExecutionStateOutputModel.graph_execution_id
                    == state.graph_execution_id.value,
                    GraphExecutionStateOutputModel.is_current.is_(True),
                )
                .values(is_current=False)
            )
        model = graph_execution_state_output_entity_to_model(state)
        self._session.add(model)

    async def delete(self, id: object) -> None:
        model = await self._session.get(GraphExecutionStateOutputModel, getattr(id, 'value', id))
        if model is not None:
            await self._session.delete(model)

    async def exists(self, id: object) -> ExistsResult:
        query = select(GraphExecutionStateOutputModel).where(GraphExecutionStateOutputModel.id == getattr(id, 'value', id))
        row = (await self._session.execute(query)).scalar_one_or_none()
        return ExistsResult(row is not None)


__all__ = [
    "GraphExecutionStateOutputModel",
    "SqlGraphExecutionStateRepository",
]
