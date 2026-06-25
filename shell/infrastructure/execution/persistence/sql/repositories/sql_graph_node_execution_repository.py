from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution import (
    GraphNodeExecution,
)
from shell.domain.execution.aggregates.graph_node_execution.repositories.graph_node_execution_repository import (
    GraphNodeExecutionRepository,
)
from shell.domain.execution.value_objects.ids import GraphExecutionId, GraphNodeExecutionId
from shell.infrastructure.execution.persistence.sql.models.graph_node_execution import (
    GraphNodeExecutionModel,
)
from sqlalchemy import select
from sqlalchemy.orm import selectinload

if TYPE_CHECKING:
    from sqlalchemy import Select
    from sqlalchemy.ext.asyncio import AsyncSession


class SqlGraphNodeExecutionRepository(GraphNodeExecutionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_query(self) -> Select[tuple[GraphNodeExecutionModel]]:
        return select(GraphNodeExecutionModel).options(
            selectinload(GraphNodeExecutionModel.input_state_models),
            selectinload(GraphNodeExecutionModel.output_state_models),
        )

    async def get_by_id(self, node_id: GraphNodeExecutionId) -> GraphNodeExecution | None:
        query = self._base_query().where(GraphNodeExecutionModel.id == node_id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return _graph_node_execution_model_to_entity(row) if row else None

    async def save(self, node: GraphNodeExecution) -> None:
        model = _graph_node_execution_entity_to_model(node)
        await self._session.merge(model)

    async def list_by_ids(self, ids: list[GraphNodeExecutionId]) -> list[GraphNodeExecution]:
        if not ids:
            return []
        id_values = [i.value for i in ids]
        query = self._base_query().where(GraphNodeExecutionModel.id.in_(id_values))
        rows = (await self._session.execute(query)).scalars().all()
        return [_graph_node_execution_model_to_entity(r) for r in rows if r is not None]

    async def list_by_graph_execution_id(
        self, graph_execution_id: GraphExecutionId
    ) -> list[GraphNodeExecution]:
        query = self._base_query().where(
            GraphNodeExecutionModel.graph_execution_id == graph_execution_id.value,
        )
        rows = (await self._session.execute(query)).scalars().all()
        return [_graph_node_execution_model_to_entity(r) for r in rows if r is not None]


def _graph_node_execution_model_to_entity(
    model: GraphNodeExecutionModel,
) -> GraphNodeExecution:
    from shell.domain.execution.aggregates.graph_node_execution.entities.graph_node_execution_state_input import (
        GraphNodeExecutionStateInput,
    )
    from shell.domain.execution.aggregates.graph_node_execution.entities.graph_node_execution_state_output import (
        GraphNodeExecutionStateOutput,
    )
    from shell.domain.execution.value_objects.ids import (
        GraphNodeExecutionStateInputId,
        GraphNodeExecutionStateOutputId,
    )
    from shell.domain.platform.value_objects.mode import Mode

    input_states = [
        GraphNodeExecutionStateInput(
            id=GraphNodeExecutionStateInputId(p.id),
            graph_node_execution_id=GraphNodeExecutionId(p.graph_node_execution_id),
            payload=dict(p.payload),
            is_current=p.is_current,
            created_at=p.created_at,
        )
        for p in model.input_state_models
    ]
    output_states = [
        GraphNodeExecutionStateOutput(
            id=GraphNodeExecutionStateOutputId(p.id),
            graph_node_execution_id=GraphNodeExecutionId(p.graph_node_execution_id),
            payload=dict(p.payload),
            is_current=p.is_current,
            created_at=p.created_at,
        )
        for p in model.output_state_models
    ]
    return GraphNodeExecution(
        id=GraphNodeExecutionId(model.id),
        graph_execution_id=(
            GraphExecutionId(model.graph_execution_id) if model.graph_execution_id else None
        ),
        role=model.role,
        position=model.position,
        mode=Mode(model.mode),
        node_type=model.node_type,
        remaining_retries=model.max_retries or 0,
        retry_delay_seconds=model.retry_delay_seconds or 0,
        timeout_seconds=model.timeout_seconds or 0,
        input_states=input_states,
        output_states=output_states,
    )


def _graph_node_execution_entity_to_model(node: GraphNodeExecution) -> GraphNodeExecutionModel:
    from shell.infrastructure.execution.persistence.sql.models.graph_node_execution_state_input import (
        GraphNodeExecutionStateInputModel,
    )
    from shell.infrastructure.execution.persistence.sql.models.graph_node_execution_state_output import (
        GraphNodeExecutionStateOutputModel,
    )

    model = GraphNodeExecutionModel(
        id=node.id.value,
        graph_execution_id=node.graph_execution_id.value if node.graph_execution_id else "",
        position=node.position,
        mode=node.mode.value,
        role=node.role,
        node_type=node.node_type,
        model="",
        command="",
        retries=0,
        log_level="INFO",
        max_step=0,
        no_ask_user=False,
        autopilot=False,
        task_execution_id="",
        source_dir="",
        status_initial="",
        timeout_seconds=node.timeout_seconds,
        max_retries=node.remaining_retries,
        retry_delay_seconds=node.retry_delay_seconds,
    )
    model.input_state_models = [
        GraphNodeExecutionStateInputModel(
            id=p.id.value,
            graph_node_execution_id=p.graph_node_execution_id.value,
            payload=p.payload,
            is_current=p.is_current.value if p.is_current else True,
            created_at=p.created_at.value if p.created_at else None,
        )
        for p in node.input_states
    ]
    model.output_state_models = [
        GraphNodeExecutionStateOutputModel(
            id=p.id.value,
            graph_node_execution_id=p.graph_node_execution_id.value,
            payload=p.payload,
            is_current=p.is_current.value if p.is_current else True,
            created_at=p.created_at.value if p.created_at else None,
        )
        for p in node.output_states
    ]
    return model
