from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
    GraphNodeExecutionId,
)
from shell.domain.execution.aggregates.graph_node_transition_execution.graph_node_transition_execution import (
    GraphNodeTransitionExecution,
)
from shell.domain.execution.aggregates.graph_node_transition_execution.value_objects.graph_node_transition_execution_id import (
    GraphNodeTransitionExecutionId,
)
from shell.domain.execution.value_objects.condition_expression import ConditionExpression
from shell.domain.execution.value_objects.edge_type import EdgeType
from shell.infrastructure.execution.persistence.sql.models.graph_node_transition_execution import (
    GraphNodeTransitionExecutionModel,
)
from sqlalchemy import select

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class SqlGraphNodeTransitionExecutionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id_: GraphNodeTransitionExecutionId) -> GraphNodeTransitionExecution | None:
        query = select(GraphNodeTransitionExecutionModel).where(
            GraphNodeTransitionExecutionModel.id == id_.value
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        return self._model_to_entity(row) if row else None

    async def list_by_graph_execution_id(
        self, graph_execution_id: GraphExecutionId
    ) -> list[GraphNodeTransitionExecution]:
        query = select(GraphNodeTransitionExecutionModel).where(
            GraphNodeTransitionExecutionModel.graph_execution_id == graph_execution_id.value
        )
        rows = (await self._session.execute(query)).scalars().all()
        return [self._model_to_entity(r) for r in rows]

    async def list_outgoing_for_node(
        self, node_id: GraphNodeExecutionId
    ) -> list[GraphNodeTransitionExecution]:
        query = select(GraphNodeTransitionExecutionModel).where(
            GraphNodeTransitionExecutionModel.source_node_execution_id == node_id.value
        )
        rows = (await self._session.execute(query)).scalars().all()
        return [self._model_to_entity(r) for r in rows]

    async def save(self, transition: GraphNodeTransitionExecution) -> None:
        model = await self._session.get(GraphNodeTransitionExecutionModel, transition.id.value)
        if model is not None:
            return
        _now = datetime.now(tz=UTC)
        model = GraphNodeTransitionExecutionModel(
            id=transition.id.value,
            graph_execution_id=transition.graph_execution_id.value,
            source_node_execution_id=transition.source_node_execution_id.value,
            target_node_execution_id=transition.target_node_execution_id.value if transition.target_node_execution_id else "",
            transition_type=transition.edge_type.value,
            priority=0,
            condition_expression=transition.condition_expression.value if transition.condition_expression else None,
            condition_language=None,
            max_loop_count=transition.max_iterations if transition.max_iterations else 0,
            label="",
            created_at=_now,
            updated_at=_now,
        )
        self._session.add(model)

    async def delete(self, id_: GraphNodeTransitionExecutionId) -> None:
        model = await self._session.get(GraphNodeTransitionExecutionModel, id_.value)
        if model:
            await self._session.delete(model)

    async def exists(self, id_: GraphNodeTransitionExecutionId) -> bool:
        query = select(GraphNodeTransitionExecutionModel.id).where(
            GraphNodeTransitionExecutionModel.id == id_.value
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        return row is not None

    def _model_to_entity(self, model: GraphNodeTransitionExecutionModel) -> GraphNodeTransitionExecution:
        return GraphNodeTransitionExecution.restore(
            id_=GraphNodeTransitionExecutionId(model.id),
            graph_execution_id=GraphExecutionId(model.graph_execution_id),
            source_node_execution_id=GraphNodeExecutionId(model.source_node_execution_id),
            edge_type=EdgeType(model.transition_type.upper()),
            target_node_execution_id=GraphNodeExecutionId(model.target_node_execution_id) if model.target_node_execution_id else None,
            condition_expression=ConditionExpression(model.condition_expression) if model.condition_expression else None,
            max_iterations=model.max_loop_count,
        )
