from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_node_execution.repositories.graph_node_execution_state_output_repository import (
    GraphNodeExecutionStateOutputRepository,
)
from shell.domain.execution.value_objects.ids import (
    GraphNodeExecutionId,  # noqa: TC002 — GraphNodeExecutionId używany w konstruktorach w repozytorium
)
from shell.infrastructure.platform.persistence.sql.mappers import (
    graph_node_execution_state_output_entity_to_model,
    graph_node_execution_state_output_model_to_entity,
)
from sqlalchemy import select

from ..models.graph_node_execution_state_output import GraphNodeExecutionStateOutputModel

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_node_execution.entities.graph_node_execution_state_output import (
        GraphNodeExecutionStateOutput,
    )
    from sqlalchemy.ext.asyncio import AsyncSession


class SqlGraphNodeExecutionStateOutputRepository(GraphNodeExecutionStateOutputRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_latest_by_node_id(
        self, graph_node_execution_id: GraphNodeExecutionId
    ) -> GraphNodeExecutionStateOutput | None:
        query = (
            select(GraphNodeExecutionStateOutputModel)
            .where(
                GraphNodeExecutionStateOutputModel.graph_node_execution_id
                == graph_node_execution_id.value,
                GraphNodeExecutionStateOutputModel.is_current.is_(True),
            )
            .limit(1)
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        return graph_node_execution_state_output_model_to_entity(row) if row else None

    async def save(self, payload: GraphNodeExecutionStateOutput) -> None:
        model = await self._session.get(GraphNodeExecutionStateOutputModel, payload.id.value)
        if model is None:
            model = graph_node_execution_state_output_entity_to_model(payload)
            self._session.add(model)
        else:
            model.payload = payload.payload
            model.is_current = payload.is_current
