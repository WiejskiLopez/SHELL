from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.execution_service.domain.execution.aggregates.graph_execution_state.repositories.graph_execution_state_repository import (
    GraphExecutionStateRepository,
)
from shell.execution_service.infrastructure.execution.graph_execution_state.persistence.sql.mappers import (
    entity_to_model,
    model_to_entity,
)
from shell.platform.domain.value_objects.exists_result import ExistsResult

from ..models.graph_execution_state import GraphExecutionStateModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.execution_service.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.execution_service.domain.execution.aggregates.graph_execution_state.graph_execution_state import (
        GraphExecutionState,
    )
    from shell.platform.domain.value_objects.state_direction import StateDirection


class SqlGraphExecutionStateRepository(GraphExecutionStateRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id: object) -> GraphExecutionState | None:
        model = await self._session.get(GraphExecutionStateModel, getattr(id, "value", id))
        return model_to_entity(model) if model else None

    async def get_current_by_graph_execution_id_and_direction(
        self, graph_execution_id: GraphExecutionId, direction: StateDirection
    ) -> GraphExecutionState | None:
        query = (
            select(GraphExecutionStateModel)
            .where(
                GraphExecutionStateModel.graph_execution_id == graph_execution_id.value,
                GraphExecutionStateModel.direction == direction.value,
            )
            .limit(1)
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        return model_to_entity(row) if row else None

    async def save(self, state: GraphExecutionState) -> None:
        existing_row = (
            await self._session.execute(
                select(GraphExecutionStateModel).where(
                    GraphExecutionStateModel.graph_execution_id == state.graph_execution_id.value,
                    GraphExecutionStateModel.direction == state.direction.value,
                )
            )
        ).scalar_one_or_none()
        if existing_row is not None:
            await self._session.delete(existing_row)
        model = entity_to_model(state)
        self._session.add(model)

    async def delete(self, id: object, now: datetime | None = None) -> None:
        if now is None:
            now = datetime.now(tz=UTC)
        model = await self._session.get(GraphExecutionStateModel, getattr(id, "value", id))
        if model is not None:
            model.deleted_at = now

    async def exists(self, id: object) -> ExistsResult:
        query = select(GraphExecutionStateModel).where(
            GraphExecutionStateModel.id == getattr(id, "value", id)
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        return ExistsResult(row is not None)


__all__ = [
    "GraphExecutionStateModel",
    "SqlGraphExecutionStateRepository",
]
