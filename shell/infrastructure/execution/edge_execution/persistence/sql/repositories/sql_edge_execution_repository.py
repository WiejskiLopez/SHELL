from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.domain.execution.aggregates.edge_execution.edge_execution import EdgeExecution
from shell.domain.execution.aggregates.edge_execution.value_objects.edge_definition_id import (
    EdgeDefinitionId,
)
from shell.domain.execution.aggregates.edge_execution.value_objects.edge_execution_id import (
    EdgeExecutionId,
)
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.deleted_at import DeletedAt
from shell.domain.platform.value_objects.updated_at import UpdatedAt
from shell.infrastructure.execution.edge_execution.persistence.sql.models.edge_execution import (
    EdgeExecutionModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )

from shell.domain.execution.value_objects.ids import NodeExecutionId


class SqlEdgeExecutionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id_: EdgeExecutionId) -> EdgeExecution | None:
        query = select(EdgeExecutionModel).where(EdgeExecutionModel.id == id_.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return _model_to_entity(row) if row else None

    async def save(self, edge: EdgeExecution) -> None:
        _now = datetime.now(tz=UTC)
        model = await self._session.get(EdgeExecutionModel, edge.id.value)
        if model is not None:
            model.edge_definition_id = edge.edge_definition_id.value
            model.source_node_execution_id = edge.source_node_execution_id.value
            model.target_node_execution_id = (
                edge.target_node_execution_id.value if edge.target_node_execution_id else None
            )
            model.updated_at = _now
            return
        model = _entity_to_model(edge, _now)
        self._session.add(model)

    async def delete(self, id_: EdgeExecutionId) -> None:
        model = await self._session.get(EdgeExecutionModel, id_.value)
        if model:
            model.deleted_at = datetime.now(tz=UTC)

    async def exists(self, id_: EdgeExecutionId) -> bool:
        query = select(EdgeExecutionModel.id).where(EdgeExecutionModel.id == id_.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return row is not None

    async def list_by_source_node(self, node_id: NodeExecutionId) -> list[EdgeExecution]:
        query = select(EdgeExecutionModel).where(
            EdgeExecutionModel.source_node_execution_id == node_id.value
        )
        rows = (await self._session.execute(query)).scalars().all()
        return [_model_to_entity(r) for r in rows]

    async def list_by_target_node(self, node_id: NodeExecutionId) -> list[EdgeExecution]:
        query = select(EdgeExecutionModel).where(
            EdgeExecutionModel.target_node_execution_id == node_id.value
        )
        rows = (await self._session.execute(query)).scalars().all()
        return [_model_to_entity(r) for r in rows]


def _model_to_entity(model: EdgeExecutionModel) -> EdgeExecution:
    return EdgeExecution.restore(
        id_=EdgeExecutionId(model.id),
        edge_definition_id=EdgeDefinitionId(model.edge_definition_id),
        source_node_execution_id=(NodeExecutionId(model.source_node_execution_id)),
        target_node_execution_id=(
            NodeExecutionId(model.target_node_execution_id)
            if model.target_node_execution_id
            else None
        ),
        created_at=CreatedAt.from_datetime(model.created_at),
        updated_at=UpdatedAt.from_datetime(model.updated_at),
        deleted_at=DeletedAt.from_datetime(model.deleted_at)
        if model.deleted_at is not None
        else None,
    )


def _entity_to_model(edge: EdgeExecution, now: datetime) -> EdgeExecutionModel:
    return EdgeExecutionModel(
        id=edge.id.value,
        edge_definition_id=edge.edge_definition_id.value,
        source_node_execution_id=edge.source_node_execution_id.value,
        target_node_execution_id=(
            edge.target_node_execution_id.value if edge.target_node_execution_id else None
        ),
        created_at=now,
        updated_at=now,
    )
