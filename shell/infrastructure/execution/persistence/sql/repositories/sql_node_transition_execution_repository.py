from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
    NodeExecutionId,
)
from shell.domain.execution.aggregates.node_transition_execution.node_transition_execution import (
    NodeTransitionExecution,
)
from shell.domain.execution.aggregates.node_transition_execution.value_objects.node_transition_execution_id import (
    NodeTransitionExecutionId,
)
from shell.domain.execution.value_objects.condition_language import ConditionLanguage
from shell.domain.execution.value_objects.current_iteration import CurrentIteration
from shell.domain.execution.value_objects.edge_type import EdgeType
from shell.domain.execution.value_objects.max_iterations import MaxIterations
from shell.domain.execution.value_objects.transition_status import TransitionStatus
from shell.domain.platform.value_objects.condition_expression import ConditionExpression
from shell.infrastructure.execution.persistence.sql.models.node_transition_execution import (
    NodeTransitionExecutionModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class SqlNodeTransitionExecutionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(
        self, id_: NodeTransitionExecutionId
    ) -> NodeTransitionExecution | None:
        query = select(NodeTransitionExecutionModel).where(
            NodeTransitionExecutionModel.id == id_.value
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        return self._model_to_entity(row) if row else None

    async def list_by_graph_execution_id(
        self, graph_execution_id: GraphExecutionId
    ) -> list[NodeTransitionExecution]:
        query = select(NodeTransitionExecutionModel).where(
            NodeTransitionExecutionModel.graph_execution_id == graph_execution_id.value
        )
        rows = (await self._session.execute(query)).scalars().all()
        return [self._model_to_entity(r) for r in rows]

    async def list_outgoing_for_node(
        self, node_id: NodeExecutionId
    ) -> list[NodeTransitionExecution]:
        query = select(NodeTransitionExecutionModel).where(
            NodeTransitionExecutionModel.source_node_execution_id == node_id.value
        )
        rows = (await self._session.execute(query)).scalars().all()
        return [self._model_to_entity(r) for r in rows]

    async def save(self, transition: NodeTransitionExecution) -> None:
        _now = datetime.now(tz=UTC)
        model = await self._session.get(NodeTransitionExecutionModel, transition.id.value)
        if model is not None:
            model.status = transition.status.value
            model.current_iteration = transition.current_iteration.value
            model.updated_at = _now
            return
        model = NodeTransitionExecutionModel(
            id=transition.id.value,
            graph_execution_id=transition.graph_execution_id.value,
            source_node_execution_id=transition.source_node_execution_id.value,
            target_node_execution_id=transition.target_node_execution_id.value
            if transition.target_node_execution_id
            else "",
            transition_type=transition.edge_type.value,
            priority=0,
            condition_expression=transition.condition_expression.value
            if transition.condition_expression
            else None,
            condition_language=transition.condition_language.value
            if transition.condition_language
            else None,
            max_loop_count=transition.max_iterations.value if transition.max_iterations else 0,
            status=transition.status.value,
            current_iteration=transition.current_iteration.value,
            label="",
            created_at=_now,
            updated_at=_now,
        )
        self._session.add(model)

    async def delete(self, id_: NodeTransitionExecutionId) -> None:
        model = await self._session.get(NodeTransitionExecutionModel, id_.value)
        if model:
            await self._session.delete(model)

    async def exists(self, id_: NodeTransitionExecutionId) -> bool:
        query = select(NodeTransitionExecutionModel.id).where(
            NodeTransitionExecutionModel.id == id_.value
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        return row is not None

    def _model_to_entity(
        self, model: NodeTransitionExecutionModel
    ) -> NodeTransitionExecution:
        return NodeTransitionExecution.restore(
            id_=NodeTransitionExecutionId(model.id),
            graph_execution_id=GraphExecutionId(model.graph_execution_id),
            source_node_execution_id=NodeExecutionId(model.source_node_execution_id)
            if model.source_node_execution_id
            else NodeExecutionId(""),
            edge_type=EdgeType(model.transition_type.upper()),
            target_node_execution_id=NodeExecutionId(model.target_node_execution_id)
            if model.target_node_execution_id
            else None,
            condition_expression=ConditionExpression(model.condition_expression)
            if model.condition_expression
            else None,
            condition_language=ConditionLanguage(model.condition_language)
            if model.condition_language
            else None,
            max_iterations=MaxIterations(model.max_loop_count),
            status=TransitionStatus(model.status) if model.status else None,
            current_iteration=CurrentIteration(model.current_iteration)
            if model.current_iteration
            else None,
        )
