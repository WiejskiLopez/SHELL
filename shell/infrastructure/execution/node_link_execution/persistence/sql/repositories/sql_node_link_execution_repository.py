from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
    NodeExecutionId,
)
from shell.domain.execution.aggregates.node_link_execution.node_link_execution import (
    NodeLinkExecution,
)
from shell.domain.execution.aggregates.node_link_execution.value_objects.node_link_execution_id import (
    NodeLinkExecutionId,
)
from shell.domain.platform.value_objects.exists_result import ExistsResult
from shell.infrastructure.execution.persistence.sql.models import (
    NodeLinkExecutionModel,
)

if TYPE_CHECKING:
    from datetime import datetime

    from sqlalchemy.ext.asyncio import AsyncSession


class SqlNodeLinkExecutionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(
        self,
        node_link_execution_id: NodeLinkExecutionId,
    ) -> NodeLinkExecution | None:
        model = await self._session.get(NodeLinkExecutionModel, node_link_execution_id.value)
        if model is None:
            return None
        return self._model_to_entity(model)

    async def list_by_graph_execution_id(
        self,
        graph_execution_id: GraphExecutionId,
    ) -> list[NodeLinkExecution]:
        stmt = select(NodeLinkExecutionModel).where(
            NodeLinkExecutionModel.graph_execution_id == graph_execution_id.value,
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]

    async def list_by_node_execution_id(
        self,
        node_execution_id: NodeExecutionId,
    ) -> list[NodeLinkExecution]:
        stmt = select(NodeLinkExecutionModel).where(
            NodeLinkExecutionModel.node_execution_id == node_execution_id.value,
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]

    async def save(self, link: NodeLinkExecution) -> None:
        model = await self._session.get(
            NodeLinkExecutionModel,
            link.id.value,
        )
        if model is None:
            model = self._entity_to_model(link)
            self._session.add(model)

    async def delete(self, id: NodeLinkExecutionId, now: datetime) -> None:
        model = await self._session.get(NodeLinkExecutionModel, id.value)
        if model is not None:
            model.deleted_at = now

    async def exists(self, id: NodeLinkExecutionId) -> ExistsResult:
        model = await self._session.get(NodeLinkExecutionModel, id.value)
        return ExistsResult(model is not None)

    def _model_to_entity(
        self,
        model: NodeLinkExecutionModel,
    ) -> NodeLinkExecution:
        return NodeLinkExecution(
            id=NodeLinkExecutionId(model.id),
            graph_execution_id=GraphExecutionId(model.graph_execution_id),
            node_execution_id=NodeExecutionId(model.node_execution_id),
        )

    def _entity_to_model(
        self,
        entity: NodeLinkExecution,
    ) -> NodeLinkExecutionModel:
        return NodeLinkExecutionModel(
            id=entity.id.value,
            graph_execution_id=entity.graph_execution_id.value,
            node_execution_id=entity.node_execution_id.value,
        )
