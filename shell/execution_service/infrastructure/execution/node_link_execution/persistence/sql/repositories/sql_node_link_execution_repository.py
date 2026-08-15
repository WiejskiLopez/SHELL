from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.execution_service.domain.execution.aggregates.node_link_execution.repositories.node_link_execution_repository import (
    NodeLinkExecutionRepository,
)
from shell.execution_service.infrastructure.execution.node_link_execution.persistence.sql.mappers import (
    node_link_execution_entity_to_model,
    node_link_execution_model_to_entity,
)
from shell.execution_service.infrastructure.execution.node_link_execution.persistence.sql.models import (
    NodeLinkExecutionModel,
)
from shell.platform.domain.value_objects.exists_result import ExistsResult

if TYPE_CHECKING:
    from datetime import datetime

    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.execution_service.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.execution_service.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )
    from shell.execution_service.domain.execution.aggregates.node_link_execution.node_link_execution import (
        NodeLinkExecution,
    )
    from shell.execution_service.domain.execution.aggregates.node_link_execution.value_objects.node_link_execution_id import (
        NodeLinkExecutionId,
    )


class SqlNodeLinkExecutionRepository(NodeLinkExecutionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(
        self,
        node_link_execution_id: NodeLinkExecutionId,
    ) -> NodeLinkExecution | None:
        model = await self._session.get(NodeLinkExecutionModel, node_link_execution_id.value)
        if model is None:
            return None
        return node_link_execution_model_to_entity(model)

    async def list_by_graph_execution_id(
        self,
        graph_execution_id: GraphExecutionId,
    ) -> list[NodeLinkExecution]:
        stmt = select(NodeLinkExecutionModel).where(
            NodeLinkExecutionModel.graph_execution_id == graph_execution_id.value,
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [node_link_execution_model_to_entity(m) for m in models]

    async def list_by_node_execution_id(
        self,
        node_execution_id: NodeExecutionId,
    ) -> list[NodeLinkExecution]:
        stmt = select(NodeLinkExecutionModel).where(
            NodeLinkExecutionModel.node_execution_id == node_execution_id.value,
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [node_link_execution_model_to_entity(m) for m in models]

    async def save(self, link: NodeLinkExecution) -> None:
        model = await self._session.get(
            NodeLinkExecutionModel,
            link.id.value,
        )
        if model is None:
            model = node_link_execution_entity_to_model(link)
            self._session.add(model)

    async def delete(self, id: NodeLinkExecutionId, now: datetime | None = None) -> None:
        model = await self._session.get(NodeLinkExecutionModel, id.value)
        if model is not None:
            model.deleted_at = now

    async def exists(self, id: NodeLinkExecutionId) -> ExistsResult:
        model = await self._session.get(NodeLinkExecutionModel, id.value)
        return ExistsResult(model is not None)
