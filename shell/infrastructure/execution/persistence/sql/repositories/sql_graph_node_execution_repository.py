from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution import (
    GraphNodeExecution,
)
from shell.domain.execution.aggregates.graph_node_execution.repositories.graph_node_execution_repository import (
    GraphNodeExecutionRepository,
)
from shell.domain.execution.value_objects.ids import GraphExecutionId, GraphNodeExecutionId
from shell.domain.execution.value_objects.node_order import NodeOrder
from shell.domain.execution.value_objects.node_type import NodeType
from shell.domain.execution.value_objects.remaining_retries import RemainingRetries
from shell.domain.execution.value_objects.retry_delay_seconds import RetryDelaySeconds
from shell.domain.execution.value_objects.timeout_seconds import TimeoutSeconds
from shell.infrastructure.execution.persistence.sql.models.graph_node_execution import (
    GraphNodeExecutionModel,
)
from sqlalchemy import select

if TYPE_CHECKING:
    from sqlalchemy import Select
    from sqlalchemy.ext.asyncio import AsyncSession


class SqlGraphNodeExecutionRepository(GraphNodeExecutionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_query(self) -> Select[tuple[GraphNodeExecutionModel]]:
        return select(GraphNodeExecutionModel)

    async def get_by_id(self, node_id: GraphNodeExecutionId) -> GraphNodeExecution | None:
        query = self._base_query().where(GraphNodeExecutionModel.id == node_id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return _graph_node_execution_model_to_entity(row) if row else None

    async def save(self, node: GraphNodeExecution) -> None:
        model = await self._session.get(GraphNodeExecutionModel, node.id.value)
        if model is None:
            model = _graph_node_execution_entity_to_model(node)
            self._session.add(model)
        else:
            model.graph_execution_id = node.graph_execution_id.value if node.graph_execution_id else ""
            model.position = node.position
            model.mode = node.mode.value
            model.role = node.role
            model.node_type = node.node_type
            model.status = node.status.value
            model.timeout_seconds = node.timeout_seconds
            model.max_retries = node.remaining_retries
            model.retry_delay_seconds = node.retry_delay_seconds

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
    from shell.domain.execution.value_objects.graph_node_execution_status import (
        GraphNodeExecutionStatus,
    )
    from shell.domain.platform.value_objects.mode import Mode

    return GraphNodeExecution(
        id=GraphNodeExecutionId(model.id),
        graph_execution_id=(
            GraphExecutionId(model.graph_execution_id) if model.graph_execution_id else None
        ),
        role=model.role,
        position=NodeOrder(model.position),
        mode=Mode(model.mode),
        node_type=NodeType(model.node_type),
        remaining_retries=RemainingRetries(model.max_retries or 0),
        retry_delay_seconds=RetryDelaySeconds(model.retry_delay_seconds or 0),
        timeout_seconds=TimeoutSeconds(model.timeout_seconds or 0),
        status=GraphNodeExecutionStatus(model.status) if model.status else None,
    )


def _graph_node_execution_entity_to_model(node: GraphNodeExecution) -> GraphNodeExecutionModel:
    model = GraphNodeExecutionModel(
        id=node.id.value,
        graph_execution_id=node.graph_execution_id.value if node.graph_execution_id else "",
        position=node.position.value,
        mode=node.mode.value,
        role=node.role,
        node_type=node.node_type.value,
        model="",
        command="",
        retries=0,
        log_level="INFO",
        max_step=0,
        no_ask_user=False,
        autopilot=False,
        task_execution_id="",
        source_dir="",
        status=node.status.value,
        status_initial="",
        timeout_seconds=node.timeout_seconds.value,
        max_retries=node.remaining_retries.value,
        retry_delay_seconds=node.retry_delay_seconds.value,
    )
    return model
