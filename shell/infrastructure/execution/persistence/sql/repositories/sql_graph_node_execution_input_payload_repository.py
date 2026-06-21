from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.repositories.graph_node_execution_input_payload_repository import (
    GraphNodeExecutionInputPayloadRepository,
)
from shell.domain.execution.value_objects.ids import (
    GraphNodeExecutionId,  # noqa: TC002 — GraphNodeExecutionId używany w konstruktorach w repozytorium
)
from shell.infrastructure.platform.persistence.sql.mappers import (
    graph_node_execution_input_payload_entity_to_model,
    graph_node_execution_input_payload_model_to_entity,
)
from sqlalchemy import select

from ..models import GraphNodeExecutionInputPayloadModel

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_node_execution_input_payload import (
        GraphNodeExecutionInputPayload,
    )
    from sqlalchemy.ext.asyncio import AsyncSession


class SqlGraphNodeExecutionInputPayloadRepository(GraphNodeExecutionInputPayloadRepository):
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
