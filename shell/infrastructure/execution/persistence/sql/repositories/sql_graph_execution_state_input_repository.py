from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_execution_state_input.ports.graph_execution_state_input_repository import (
    GraphExecutionStateInputRepository,
)
from shell.domain.execution.value_objects.ids import (
    GraphExecutionId,  # noqa: TC002 — GraphExecutionId używany w konstruktorach w repozytorium
)
from shell.infrastructure.platform.persistence.sql.mappers import (
    graph_execution_state_input_entity_to_model,
    graph_execution_state_input_model_to_entity,
)
from sqlalchemy import select, update

from ..models.graph_execution_state_input import GraphExecutionStateInputModel

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution_state_input.graph_execution_state_input import (
        GraphExecutionStateInput,
    )
    from sqlalchemy.ext.asyncio import AsyncSession


class SqlGraphExecutionStateInputRepository(GraphExecutionStateInputRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_current_by_graph_execution_id(
        self, graph_execution_id: GraphExecutionId
    ) -> GraphExecutionStateInput | None:
        query = (
            select(GraphExecutionStateInputModel)
            .where(
                GraphExecutionStateInputModel.graph_execution_id == graph_execution_id.value,
                GraphExecutionStateInputModel.is_current.is_(True),
            )
            .limit(1)
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        return graph_execution_state_input_model_to_entity(row) if row else None

    async def save(self, state: GraphExecutionStateInput) -> None:
        if state.is_current:
            await self._session.execute(
                update(GraphExecutionStateInputModel)
                .where(
                    GraphExecutionStateInputModel.graph_execution_id == state.graph_execution_id.value,
                    GraphExecutionStateInputModel.is_current.is_(True),
                )
                .values(is_current=False)
            )
        model = graph_execution_state_input_entity_to_model(state)
        self._session.add(model)
