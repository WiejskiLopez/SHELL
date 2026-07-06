from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.domain.execution.aggregates.edge_link_execution.edge_link_execution import (
    EdgeLinkExecution,
)
from shell.domain.execution.aggregates.edge_link_execution.value_objects.edge_link_execution_id import (
    EdgeLinkExecutionId,
)
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.deleted_at import DeletedAt
from shell.domain.platform.value_objects.updated_at import UpdatedAt
from shell.infrastructure.execution.edge_link_execution.persistence.sql.models.edge_link_execution import (
    EdgeLinkExecutionModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


from shell.domain.execution.aggregates.edge_execution.value_objects.edge_execution_id import (
    EdgeExecutionId,
)
from shell.domain.execution.value_objects.ids import NodeExecutionId


class SqlEdgeLinkExecutionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id_: EdgeLinkExecutionId) -> EdgeLinkExecution | None:
        model = await self._session.get(EdgeLinkExecutionModel, id_.value)
        return _model_to_entity(model) if model else None

    async def save(self, link: EdgeLinkExecution) -> None:
        _now = datetime.now(tz=UTC)
        model = await self._session.get(EdgeLinkExecutionModel, link.id.value)
        if model is not None:
            model.node_execution_id = link.node_execution_id.value
            model.edge_execution_id = link.edge_execution_id.value
            model.updated_at = _now
            return
        model = _entity_to_model(link, _now)
        self._session.add(model)

    async def delete(self, id_: EdgeLinkExecutionId) -> None:
        model = await self._session.get(EdgeLinkExecutionModel, id_.value)
        if model:
            model.deleted_at = datetime.now(tz=UTC)

    async def exists(self, id_: EdgeLinkExecutionId) -> bool:
        model = await self._session.get(EdgeLinkExecutionModel, id_.value)
        return model is not None

    async def list_by_node_execution_id(
        self, node_execution_id: NodeExecutionId
    ) -> list[EdgeLinkExecution]:
        stmt = select(EdgeLinkExecutionModel).where(
            EdgeLinkExecutionModel.node_execution_id == node_execution_id.value,
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [_model_to_entity(m) for m in models]

    async def list_by_edge_execution_id(
        self, edge_execution_id: EdgeExecutionId
    ) -> list[EdgeLinkExecution]:
        stmt = select(EdgeLinkExecutionModel).where(
            EdgeLinkExecutionModel.edge_execution_id == edge_execution_id.value,
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [_model_to_entity(m) for m in models]


def _model_to_entity(model: EdgeLinkExecutionModel) -> EdgeLinkExecution:
    return EdgeLinkExecution.restore(
        id_=EdgeLinkExecutionId(model.id),
        node_execution_id=NodeExecutionId(model.node_execution_id),
        edge_execution_id=EdgeExecutionId(model.edge_execution_id),
        created_at=CreatedAt.from_datetime(model.created_at),
        updated_at=UpdatedAt.from_datetime(model.updated_at),
        deleted_at=DeletedAt.from_datetime(model.deleted_at)
        if model.deleted_at is not None
        else None,
    )


def _entity_to_model(link: EdgeLinkExecution, now: datetime) -> EdgeLinkExecutionModel:
    return EdgeLinkExecutionModel(
        id=link.id.value,
        node_execution_id=link.node_execution_id.value,
        edge_execution_id=link.edge_execution_id.value,
        created_at=now,
        updated_at=now,
    )
