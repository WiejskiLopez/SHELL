from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.domain.execution.aggregates.graph_node_link_execution.value_objects.graph_node_link_execution_id import (
    GraphNodeLinkExecutionId,
)
from shell.domain.platform.value_objects.exists_result import ExistsResult
from shell.infrastructure.execution.persistence.sql.models import (
    GraphNodeLinkExecutionModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
        GraphNodeExecutionId,
    )
    from shell.domain.execution.aggregates.graph_node_link_execution.graph_node_link_execution import (
        GraphNodeLinkExecution,
    )


class SqlGraphNodeLinkExecutionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(
        self,
        graph_node_link_execution_id: GraphNodeLinkExecutionId,
    ) -> GraphNodeLinkExecution | None:
        model = await self._session.get(
            GraphNodeLinkExecutionModel, graph_node_link_execution_id.value
        )
        if model is None:
            return None
        return self._model_to_entity(model)

    async def list_by_graph_execution_id(
        self,
        graph_execution_id: GraphExecutionId,
    ) -> list[GraphNodeLinkExecution]:
        stmt = select(GraphNodeLinkExecutionModel).where(
            GraphNodeLinkExecutionModel.graph_execution_id == graph_execution_id.value,
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]

    async def list_by_graph_node_execution_id(
        self,
        graph_node_execution_id: GraphNodeExecutionId,
    ) -> list[GraphNodeLinkExecution]:
        stmt = select(GraphNodeLinkExecutionModel).where(
            GraphNodeLinkExecutionModel.graph_node_execution_id
            == graph_node_execution_id.value,
        )
        result = await self._session.execute(stmt)
        models = result.scalars().all()
        return [self._model_to_entity(m) for m in models]

    async def save(self, link: GraphNodeLinkExecution) -> None:
        model = await self._session.get(
            GraphNodeLinkExecutionModel,
            link.id.value,
        )
        if model is None:
            model = self._entity_to_model(link)
            self._session.add(model)

    async def delete(self, id: GraphNodeLinkExecutionId) -> None:
        model = await self._session.get(GraphNodeLinkExecutionModel, id.value)
        if model is not None:
            await self._session.delete(model)

    async def exists(self, id: GraphNodeLinkExecutionId) -> ExistsResult:
        model = await self._session.get(GraphNodeLinkExecutionModel, id.value)
        return ExistsResult(model is not None)

    def _model_to_entity(
        self,
        model: GraphNodeLinkExecutionModel,
    ) -> GraphNodeLinkExecution:
        return GraphNodeLinkExecution(
            id=GraphNodeLinkExecutionId(model.id),
            graph_execution_id=GraphExecutionId(model.graph_execution_id),
            graph_node_execution_id=GraphNodeExecutionId(model.graph_node_execution_id),
        )

    def _entity_to_model(
        self,
        entity: GraphNodeLinkExecution,
    ) -> GraphNodeLinkExecutionModel:
        return GraphNodeLinkExecutionModel(
            id=entity.id.value,
            graph_execution_id=entity.graph_execution_id.value,
            graph_node_execution_id=entity.graph_node_execution_id.value,
        )
