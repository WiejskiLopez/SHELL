from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from shell.domain.value_objects.ids import WorkflowId

from ..mappers import (
    workflow_entity_to_model,
    workflow_model_to_entity,
)
from ..models import WorkflowModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.domain.aggregates.workflow import Workflow


class SqlWorkflowRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, workflow_id: WorkflowId) -> Workflow | None:
        query = (
            select(WorkflowModel)
            .options(
                selectinload(WorkflowModel.graph_node_execution_state_models),
                selectinload(WorkflowModel.graph_node_execution_result_models),
            )
            .where(WorkflowModel.id == workflow_id.value)
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        return workflow_model_to_entity(row) if row else None

    async def save(self, workflow: Workflow) -> None:
        from shell.domain.exceptions import WorkflowConcurrentlyModified

        existing = await self._session.execute(
            select(WorkflowModel.version).where(WorkflowModel.id == workflow.id.value)
        )
        existing_version = existing.scalar_one_or_none()

        if existing_version is None:
            workflow.version = max(workflow.version, 0) + 1
            model = workflow_entity_to_model(workflow)
            await self._session.merge(model)
            return

        if existing_version != workflow.version:
            raise WorkflowConcurrentlyModified(workflow.id.value)

        new_version = workflow.version + 1
        cas_stmt = (
            update(WorkflowModel)
            .where(
                WorkflowModel.id == workflow.id.value,
                WorkflowModel.version == workflow.version,
            )
            .values(
                status=workflow.status.value,
                current_graph_node_execution_id=(
                    workflow.cursor.current_graph_node_execution_id.value
                    if workflow.cursor.current_graph_node_execution_id
                    else None
                ),
                work_dir=workflow.execution_context.work_dir,
                correlation_id=workflow.execution_context.correlation_id,
                version=new_version,
            )
        )
        result = await self._session.execute(cas_stmt)
        if (result.rowcount if hasattr(result, "rowcount") else 0) == 0:
            raise WorkflowConcurrentlyModified(workflow.id.value)

        workflow.version = new_version
        model = workflow_entity_to_model(workflow)
        await self._session.merge(model)
