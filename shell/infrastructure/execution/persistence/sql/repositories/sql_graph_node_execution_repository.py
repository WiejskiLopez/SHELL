from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution import (
    GraphNodeExecution,
)
from shell.domain.execution.aggregates.graph_node_execution.repositories.graph_node_execution_repository import (
    GraphNodeExecutionRepository,
)
from shell.domain.execution.value_objects.ids import GraphNodeExecutionId
from shell.domain.execution.value_objects.node_order import NodeOrder
from shell.domain.execution.value_objects.node_type import NodeType
from shell.infrastructure.execution.persistence.sql.models.graph_node_execution import (
    GraphNodeExecutionModel,
)
from shell.infrastructure.execution.persistence.sql.models.graph_node_link_execution import (
    GraphNodeLinkExecutionModel,
)

if TYPE_CHECKING:
    from sqlalchemy import Select
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )


from shell.domain.execution.value_objects.graph_node_execution_status import (
        GraphNodeExecutionStatus,
    )
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
            model.position = node.position.value
            model.mode = node.mode.value
            model.role = node.role.value
            model.node_type = node.node_type.value
            model.status = node.status.value

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
        stmt = (
            select(GraphNodeExecutionModel)
            .join(
                GraphNodeLinkExecutionModel,
                GraphNodeLinkExecutionModel.graph_node_execution_id == GraphNodeExecutionModel.id,
            )
            .where(GraphNodeLinkExecutionModel.graph_execution_id == graph_execution_id.value)
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return [_graph_node_execution_model_to_entity(r) for r in rows if r is not None]


def _graph_node_execution_model_to_entity(
    model: GraphNodeExecutionModel,
) -> GraphNodeExecution:
    return GraphNodeExecution(
        id=GraphNodeExecutionId(model.id),
        role=NodeRole(model.role) if model.role else NodeRole.PLANNER,
        position=NodeOrder(model.position),
        mode=Mode(model.mode),
        node_type=NodeType(model.node_type),
        status=GraphNodeExecutionStatus(model.status) if model.status else None,
    )


def _graph_node_execution_entity_to_model(node: GraphNodeExecution) -> GraphNodeExecutionModel:
    model = GraphNodeExecutionModel(
        id=node.id.value,
        position=node.position.value,
        mode=node.mode.value,
        role=node.role.value,
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
    )
    return model
