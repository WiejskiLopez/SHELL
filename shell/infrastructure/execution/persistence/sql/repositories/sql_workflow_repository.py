from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.session_execution.value_objects.session_execution_id import (
    SessionExecutionId,
)
from shell.domain.execution.aggregates.workflow.repositories.workflow_repository import (
    WorkflowRepository,
)
from shell.domain.execution.value_objects.ids import (
    WorkflowId,  # noqa: TC002 — WorkflowId używany w konstruktorach w repozytorium
)
from shell.domain.execution.value_objects.session_id_ref import SessionIdRef
from shell.infrastructure.execution.persistence.sql.mappers import (
    workflow_entity_to_model,
    workflow_model_to_entity,
    workflow_update_model,
)
from sqlalchemy import select

from ..models import WorkflowModel

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.workflow import Workflow
    from sqlalchemy.ext.asyncio import AsyncSession


class SqlWorkflowRepository(WorkflowRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, workflow_id: WorkflowId) -> Workflow | None:
        query = select(WorkflowModel).where(WorkflowModel.id == workflow_id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return workflow_model_to_entity(row) if row else None

    async def get_by_session_id(self, session_id: SessionIdRef) -> list[Workflow]:
        query = select(WorkflowModel).where(WorkflowModel.session_id == session_id.value)
        rows = (await self._session.execute(query)).scalars().all()
        return [workflow_model_to_entity(row) for row in rows if row]

    async def get_by_session_execution_id(
        self, session_execution_id: SessionExecutionId
    ) -> list[Workflow]:
        query = select(WorkflowModel).where(
            WorkflowModel.session_execution_id == session_execution_id.value
        )
        rows = (await self._session.execute(query)).scalars().all()
        return [workflow_model_to_entity(row) for row in rows if row]

    async def save(self, workflow: Workflow) -> None:
        model = await self._session.get(WorkflowModel, workflow.id.value)
        if model is None:
            model = workflow_entity_to_model(workflow)
            self._session.add(model)
        else:
            workflow_update_model(model, workflow)


__all__ = [
    "SqlWorkflowRepository",
    "WorkflowModel",
]
