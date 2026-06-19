from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.domain.execution.repositories.graph_node_execution_output_payload_repository import GraphNodeExecutionOutputPayloadRepository
from shell.domain.platform.value_objects.ids import GraphNodeExecutionId

from shell.infrastructure.platform.persistence.sql.mappers import (
    graph_node_execution_output_payload_entity_to_model,
    graph_node_execution_output_payload_model_to_entity,
)
from ..models import GraphNodeExecutionOutputPayloadModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.domain.execution.aggregates.graph_node_execution_output_payload import (
        GraphNodeExecutionOutputPayload,
    )


class SqlGraphNodeExecutionOutputPayloadRepository(GraphNodeExecutionOutputPayloadRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_latest_by_node_id(
        self, graph_node_execution_id: GraphNodeExecutionId
    ) -> GraphNodeExecutionOutputPayload | None:
        query = (
            select(GraphNodeExecutionOutputPayloadModel)
            .where(
                GraphNodeExecutionOutputPayloadModel.graph_node_execution_id == graph_node_execution_id.value,
                GraphNodeExecutionOutputPayloadModel.is_current.is_(True),
            )
            .limit(1)
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        return graph_node_execution_output_payload_model_to_entity(row) if row else None

    async def save(self, payload: GraphNodeExecutionOutputPayload) -> None:
        model = graph_node_execution_output_payload_entity_to_model(payload)
        await self._session.merge(model)
