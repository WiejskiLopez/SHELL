from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.domain.execution.aggregates.edge_execution.edge_execution import EdgeExecution
from shell.domain.execution.aggregates.edge_execution.repositories.edge_execution_repository import (
    EdgeExecutionRepository,
)
from shell.domain.execution.aggregates.edge_execution.value_objects.edge_execution_id import (
    EdgeExecutionId,
)
from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
    NodeExecutionId,
)
from shell.infrastructure.execution.edge_execution.persistence.sql.mappers import (
    edge_execution_entity_to_model,
    edge_execution_model_to_entity,
    edge_execution_update_model,
)
from shell.infrastructure.execution.edge_execution.persistence.sql.models.edge_execution import (
    EdgeExecutionModel,
)
from shell.platform.domain.value_objects.exists_result import ExistsResult

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class SqlEdgeExecutionRepository(EdgeExecutionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id_: EdgeExecutionId) -> EdgeExecution | None:
        query = select(EdgeExecutionModel).where(EdgeExecutionModel.id == id_.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return edge_execution_model_to_entity(row) if row else None

    async def save(self, edge: EdgeExecution) -> None:
        _now = datetime.now(tz=UTC)
        model = await self._session.get(EdgeExecutionModel, edge.id.value)
        if model is not None:
            edge_execution_update_model(model, edge, _now)
            return
        model = edge_execution_entity_to_model(edge, _now)
        self._session.add(model)

    async def delete(self, id_: EdgeExecutionId) -> None:
        model = await self._session.get(EdgeExecutionModel, id_.value)
        if model:
            model.deleted_at = datetime.now(tz=UTC)

    async def exists(self, id_: EdgeExecutionId) -> ExistsResult:
        query = select(EdgeExecutionModel.id).where(EdgeExecutionModel.id == id_.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return ExistsResult(row is not None)

    async def list_by_source_node(self, node_id: NodeExecutionId) -> list[EdgeExecution]:
        query = select(EdgeExecutionModel).where(
            EdgeExecutionModel.source_node_execution_id == node_id.value
        )
        rows = (await self._session.execute(query)).scalars().all()
        return [edge_execution_model_to_entity(r) for r in rows]

    async def list_by_target_node(self, node_id: NodeExecutionId) -> list[EdgeExecution]:
        query = select(EdgeExecutionModel).where(
            EdgeExecutionModel.target_node_execution_id == node_id.value
        )
        rows = (await self._session.execute(query)).scalars().all()
        return [edge_execution_model_to_entity(r) for r in rows]
