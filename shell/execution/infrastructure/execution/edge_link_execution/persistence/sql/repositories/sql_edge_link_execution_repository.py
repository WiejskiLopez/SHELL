from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.execution.domain.execution.aggregates.edge_link_execution.repositories.edge_link_execution_repository import (
    EdgeLinkExecutionRepository,
)
from shell.execution.infrastructure.execution.edge_link_execution.persistence.sql.mappers import (
    edge_link_execution_entity_to_model,
    edge_link_execution_model_to_entity,
    edge_link_execution_update_model,
)
from shell.execution.infrastructure.execution.edge_link_execution.persistence.sql.models.edge_link_execution import (
    EdgeLinkExecutionModel,
)
from shell.platform.domain.value_objects.exists_result import ExistsResult

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.execution.domain.execution.aggregates.edge_execution.value_objects.edge_execution_id import (
        EdgeExecutionId,
    )
    from shell.execution.domain.execution.aggregates.edge_link_execution.edge_link_execution import (
        EdgeLinkExecution,
    )
    from shell.execution.domain.execution.aggregates.edge_link_execution.value_objects.edge_link_execution_id import (
        EdgeLinkExecutionId,
    )
    from shell.execution.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )


class SqlEdgeLinkExecutionRepository(EdgeLinkExecutionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id_: EdgeLinkExecutionId) -> EdgeLinkExecution | None:
        model = await self._session.get(EdgeLinkExecutionModel, id_.value)
        return edge_link_execution_model_to_entity(model) if model else None

    async def save(self, link: EdgeLinkExecution) -> None:
        _now = datetime.now(tz=UTC)
        model = await self._session.get(EdgeLinkExecutionModel, link.id.value)
        if model is not None:
            edge_link_execution_update_model(model, link, _now)
            return
        model = edge_link_execution_entity_to_model(link, _now)
        self._session.add(model)

    async def delete(self, id_: EdgeLinkExecutionId) -> None:
        model = await self._session.get(EdgeLinkExecutionModel, id_.value)
        if model:
            model.deleted_at = datetime.now(tz=UTC)

    async def exists(self, id_: EdgeLinkExecutionId) -> ExistsResult:
        model = await self._session.get(EdgeLinkExecutionModel, id_.value)
        return ExistsResult(model is not None)

    async def list_by_node_execution_id(
        self, node_execution_id: NodeExecutionId
    ) -> list[EdgeLinkExecution]:
        stmt = select(EdgeLinkExecutionModel).where(
            EdgeLinkExecutionModel.node_execution_id == node_execution_id.value,
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [edge_link_execution_model_to_entity(m) for m in models]

    async def list_by_edge_execution_id(
        self, edge_execution_id: EdgeExecutionId
    ) -> list[EdgeLinkExecution]:
        stmt = select(EdgeLinkExecutionModel).where(
            EdgeLinkExecutionModel.edge_execution_id == edge_execution_id.value,
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [edge_link_execution_model_to_entity(m) for m in models]
