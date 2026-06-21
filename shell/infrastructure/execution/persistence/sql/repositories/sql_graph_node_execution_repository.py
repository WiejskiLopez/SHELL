from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_node_execution import GraphNodeExecution
from shell.domain.execution.repositories.graph_node_execution_repository import (
    GraphNodeExecutionRepository,
)
from shell.domain.execution.value_objects.ids import GraphExecutionId, GraphNodeExecutionId
from shell.infrastructure.execution.persistence.sql.models.graph_node_execution import (
    GraphNodeExecutionModel,
)
from sqlalchemy import select
from sqlalchemy.orm import selectinload

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class SqlGraphNodeExecutionRepository(GraphNodeExecutionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_query(self):
        return select(GraphNodeExecutionModel).options(
            selectinload(GraphNodeExecutionModel.input_payload_models),
            selectinload(GraphNodeExecutionModel.output_payload_models),
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
    from shell.domain.execution.entities.graph_node_execution_input_payload import (
        GraphNodeExecutionInputPayload,
    )
    from shell.domain.execution.entities.graph_node_execution_output_payload import (
        GraphNodeExecutionOutputPayload,
    )
    from shell.domain.execution.value_objects.ids import (
        GraphNodeExecutionInputPayloadId,
        GraphNodeExecutionOutputPayloadId,
    )
    from shell.domain.platform.value_objects.mode import Mode

    input_payloads = [
        GraphNodeExecutionInputPayload(
            id=GraphNodeExecutionInputPayloadId(p.id),
            graph_node_execution_id=GraphNodeExecutionId(p.graph_node_execution_id),
            payload=dict(p.payload),
            is_current=p.is_current,
            created_at=p.created_at,
        )
        for p in model.input_payload_models
    ]
    output_payloads = [
        GraphNodeExecutionOutputPayload(
            id=GraphNodeExecutionOutputPayloadId(p.id),
            graph_node_execution_id=GraphNodeExecutionId(p.graph_node_execution_id),
            payload=dict(p.payload),
            is_current=p.is_current,
            created_at=p.created_at,
        )
        for p in model.output_payload_models
    ]
    return GraphNodeExecution(
        id=GraphNodeExecutionId(model.id),
        position=model.position,
        mode=Mode(model.mode),
        role=model.role,
        node_type=model.node_type,
        model=model.model,
        command=model.command,
        timeout=model.timeout,
        retries=model.retries,
        log_level=model.log_level,
        max_step=model.max_step,
        no_ask_user=model.no_ask_user,
        autopilot=model.autopilot,
        task_execution_id=model.task_execution_id,
        source_dir=model.source_dir,
        status_initial=model.status_initial,
        sub_graph_definition_id=model.sub_graph_definition_id,
        sub_graph_definition_version=model.sub_graph_definition_version,
        timeout_seconds=model.timeout_seconds,
        max_retries=model.max_retries,
        retry_delay_seconds=model.retry_delay_seconds,
        extra=dict(model.extra),
        graph_execution_id=(
            GraphExecutionId(model.graph_execution_id)
            if model.graph_execution_id
            else None
        ),
        input_payloads=input_payloads,
        output_payloads=output_payloads,
    )


def _graph_node_execution_entity_to_model(node: GraphNodeExecution) -> GraphNodeExecutionModel:
    from shell.infrastructure.execution.persistence.sql.models.graph_node_execution_input_payload import (
        GraphNodeExecutionInputPayloadModel,
    )
    from shell.infrastructure.execution.persistence.sql.models.graph_node_execution_output_payload import (
        GraphNodeExecutionOutputPayloadModel,
    )

    model = GraphNodeExecutionModel(
        id=node.id.value,
        graph_execution_id=node.graph_execution_id.value if node.graph_execution_id else "",
        position=node.position,
        mode=node.mode.value,
        role=node.role,
        node_type=node.node_type,
        model=node.model,
        command=node.command,
        timeout=node.timeout,
        retries=node.retries,
        log_level=node.log_level,
        max_step=node.max_step,
        no_ask_user=node.no_ask_user,
        autopilot=node.autopilot,
        task_execution_id=node.task_execution_id,
        source_dir=node.source_dir,
        status_initial=node.status_initial,
        sub_graph_definition_id=node.sub_graph_definition_id,
        sub_graph_definition_version=node.sub_graph_definition_version,
        timeout_seconds=node.timeout_seconds,
        max_retries=node.max_retries,
        retry_delay_seconds=node.retry_delay_seconds,
        extra=node.extra,
    )
    model.input_payload_models = [
        GraphNodeExecutionInputPayloadModel(
            id=p.id.value,
            graph_node_execution_id=p.graph_node_execution_id.value,
            payload=p.payload,
            is_current=p.is_current,
            created_at=p.created_at,
        )
        for p in node.input_payloads
    ]
    model.output_payload_models = [
        GraphNodeExecutionOutputPayloadModel(
            id=p.id.value,
            graph_node_execution_id=p.graph_node_execution_id.value,
            payload=p.payload,
            is_current=p.is_current,
            created_at=p.created_at,
        )
        for p in node.output_payloads
    ]
    return model
