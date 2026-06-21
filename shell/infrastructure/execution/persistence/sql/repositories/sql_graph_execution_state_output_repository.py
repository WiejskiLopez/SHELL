from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.repositories.graph_execution_state_output_repository import (
    GraphExecutionStateOutputRepository,
)
from shell.domain.execution.value_objects.ids import (
    GraphExecutionId,  # noqa: TC002 — GraphExecutionId używany w konstruktorach w repozytorium
)
from shell.infrastructure.platform.persistence.sql.mappers import (
    graph_execution_state_output_entity_to_model,
    graph_execution_state_output_model_to_entity,
)
from sqlalchemy import select, update

from ..models.graph_execution_state_output import GraphExecutionStateOutputModel

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution.graph_execution_state_output import (
        GraphExecutionStateOutput,
    )
    from sqlalchemy.ext.asyncio import AsyncSession


class SqlGraphExecutionStateOutputRepository(GraphExecutionStateOutputRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_current_by_graph_execution_id(
        self, graph_execution_id: GraphExecutionId
    ) -> GraphExecutionStateOutput | None:
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

    async def save(self, state: GraphExecutionStateOutput) -> None:
        if state.is_current:
            await self._session.execute(
                update(GraphExecutionStateOutputModel)
                .where(
                    GraphExecutionStateOutputModel.graph_execution_id == state.graph_execution_id.value,
                    GraphExecutionStateOutputModel.is_current.is_(True),
                )
                .values(is_current=False)
            )
        model = graph_execution_state_output_entity_to_model(state)
        self._session.add(model)
