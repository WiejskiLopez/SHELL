from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_node_execution.repositories.graph_node_execution_state_input_repository import (
    GraphNodeExecutionStateInputRepository,
)
from shell.domain.execution.value_objects.ids import (
    GraphNodeExecutionId,  # noqa: TC002 — GraphNodeExecutionId używany w konstruktorach w repozytorium
)
from shell.infrastructure.platform.persistence.sql.mappers import (
    graph_node_execution_state_input_entity_to_model,
    graph_node_execution_state_input_model_to_entity,
)
from sqlalchemy import select

from ..models.graph_node_execution_state_input import GraphNodeExecutionStateInputModel

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_node_execution.entities.graph_node_execution_state_input import (
        GraphNodeExecutionStateInput,
    )
    from sqlalchemy.ext.asyncio import AsyncSession


class SqlGraphNodeExecutionStateInputRepository(GraphNodeExecutionStateInputRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_latest_by_node_id(
        self, graph_node_execution_id: GraphNodeExecutionId
    ) -> GraphNodeExecutionStateInput | None:
        query = (
            select(GraphNodeExecutionStateInputModel)
            .where(
                GraphNodeExecutionStateInputModel.graph_node_execution_id
                == graph_node_execution_id.value,
                GraphNodeExecutionStateInputModel.is_current.is_(True),
            )
            .limit(1)
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        return graph_node_execution_state_input_model_to_entity(row) if row else None

    async def save(self, payload: GraphNodeExecutionStateInput) -> None:
        model = graph_node_execution_state_input_entity_to_model(payload)
        await self._session.merge(model)
