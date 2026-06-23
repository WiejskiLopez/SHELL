from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.session.session_id import SessionId
from shell.domain.execution.aggregates.workflow.ports.workflow_repository import WorkflowRepository
from shell.domain.execution.value_objects.ids import (
    WorkflowId,  # noqa: TC002 — WorkflowId używany w konstruktorach w repozytorium
)
from shell.infrastructure.platform.persistence.sql.mappers import (
    workflow_entity_to_model,
    workflow_model_to_entity,
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

    async def get_by_session_id(self, session_id: SessionId) -> list[Workflow]:
        query = select(WorkflowModel).where(WorkflowModel.session_id == session_id.value)
        rows = (await self._session.execute(query)).scalars().all()
        return [workflow_model_to_entity(row) for row in rows if row]

    async def save(self, workflow: Workflow) -> None:
        model = workflow_entity_to_model(workflow)
        await self._session.merge(model)


__all__ = [
    "SqlWorkflowRepository",
    "WorkflowModel",
]
