from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.workflow.ports.workflow_repository import WorkflowRepository
from shell.domain.execution.value_objects.ids import (
    WorkflowId,  # noqa: TC002 — WorkflowId używany w konstruktorach w repozytorium
)
from shell.infrastructure.platform.persistence.sql.mappers import (
    workflow_entity_to_model,
    workflow_model_to_entity,
)
from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from ..models import WorkflowModel

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.workflow import Workflow
    from sqlalchemy.ext.asyncio import AsyncSession


class SqlWorkflowRepository(WorkflowRepository):
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
        from shell.domain.execution.exceptions import WorkflowConcurrentlyModified

        existing = await self._session.execute(
            select(WorkflowModel.version).where(WorkflowModel.id == workflow.id.value)
        )
        existing_version = existing.scalar_one_or_none()

        if existing_version is None:
            new_version = max(workflow.version, 0) + 1
            workflow.apply_new_version(new_version)
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
                correlation_id=workflow.execution_context.correlation_id,
                version=new_version,
            )
        )
        result = await self._session.execute(cas_stmt)
        if (result.rowcount if hasattr(result, "rowcount") else 0) == 0:
            raise WorkflowConcurrentlyModified(workflow.id.value)

        workflow.apply_new_version(new_version)
        model = workflow_entity_to_model(workflow)
        await self._session.merge(model)
