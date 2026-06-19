from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.domain.value_objects.ids import GraphNodeExecutionId

from ..mappers import (
    graph_node_execution_input_payload_entity_to_model,
    graph_node_execution_input_payload_model_to_entity,
)
from ..models import GraphNodeExecutionInputPayloadModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.domain.aggregates.graph_node_execution_input_payload import (
        GraphNodeExecutionInputPayload,
    )


class SqlGraphNodeExecutionInputPayloadRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_latest_by_node_id(
        self, graph_node_execution_id: GraphNodeExecutionId
    ) -> GraphNodeExecutionInputPayload | None:
        query = (
            select(GraphNodeExecutionInputPayloadModel)
            .where(
                GraphNodeExecutionInputPayloadModel.graph_node_execution_id == graph_node_execution_id.value,
                GraphNodeExecutionInputPayloadModel.is_current.is_(True),
            )
            .limit(1)
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        return graph_node_execution_input_payload_model_to_entity(row) if row else None

    async def save(self, payload: GraphNodeExecutionInputPayload) -> None:
        model = graph_node_execution_input_payload_entity_to_model(payload)
        await self._session.merge(model)
