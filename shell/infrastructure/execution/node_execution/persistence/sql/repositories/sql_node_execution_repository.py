from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.domain.execution.aggregates.node_execution.node_execution import (
    NodeExecution,
)
from shell.domain.execution.aggregates.node_execution.repositories.node_execution_repository import (
    NodeExecutionRepository,
)
from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
    NodeExecutionId,
)
from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_status import (
    NodeExecutionStatus,
)
from shell.domain.execution.aggregates.node_execution.value_objects.node_order import NodeOrder
from shell.domain.execution.aggregates.node_execution.value_objects.node_type import NodeType
from shell.infrastructure.execution.node_execution.persistence.sql.models.node_execution import (
    NodeExecutionModel,
)
from shell.infrastructure.execution.node_link_execution.persistence.sql.models.node_link_execution import (
    NodeLinkExecutionModel,
)
from shell.platform.domain.value_objects.created_at import CreatedAt

if TYPE_CHECKING:
    from sqlalchemy import Select
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )


class SqlNodeExecutionRepository(NodeExecutionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_query(self) -> Select[tuple[NodeExecutionModel]]:
        return select(NodeExecutionModel)

    async def get_by_id(self, node_id: NodeExecutionId) -> NodeExecution | None:
        query = self._base_query().where(NodeExecutionModel.id == node_id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return _node_execution_model_to_entity(row) if row else None

    async def save(self, node: NodeExecution) -> None:
        model = await self._session.get(NodeExecutionModel, node.id.value)
        if model is None:
            model = _node_execution_entity_to_model(node)
            self._session.add(model)
        else:
            model.position = node.order.value
            model.node_type = node.node_type.value
            model.created_at = node.created_at.value
            model.status = node.status.value

    async def list_by_ids(self, ids: list[NodeExecutionId]) -> list[NodeExecution]:
        if not ids:
            return []
        id_values = [i.value for i in ids]
        query = self._base_query().where(NodeExecutionModel.id.in_(id_values))
        rows = (await self._session.execute(query)).scalars().all()
        return [_node_execution_model_to_entity(r) for r in rows if r is not None]

    async def list_by_graph_execution_id(
        self, graph_execution_id: GraphExecutionId
    ) -> list[NodeExecution]:
        stmt = (
            select(NodeExecutionModel)
            .join(
                NodeLinkExecutionModel,
                NodeLinkExecutionModel.node_execution_id == NodeExecutionModel.id,
            )
            .where(NodeLinkExecutionModel.graph_execution_id == graph_execution_id.value)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_node_execution_model_to_entity(r) for r in rows if r is not None]


def _node_execution_model_to_entity(
    model: NodeExecutionModel,
) -> NodeExecution:
    return NodeExecution(
        id=NodeExecutionId(model.id),
        order=NodeOrder(model.position),
        node_type=NodeType(model.node_type),
        status=NodeExecutionStatus(model.status),
        created_at=CreatedAt.from_datetime(model.created_at)
        if model.created_at
        else CreatedAt.from_datetime(datetime.now(UTC)),
    )


def _node_execution_entity_to_model(node: NodeExecution) -> NodeExecutionModel:
    model = NodeExecutionModel(
        id=node.id.value,
        position=node.order.value,
        node_type=node.node_type.value,
        created_at=node.created_at.value,
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
    )
    return model
