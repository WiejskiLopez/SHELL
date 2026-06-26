from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId
from shell.domain.execution.aggregates.workflow_state.repositories.workflow_state_repository import (
    WorkflowStateRepository,
)
from shell.domain.execution.value_objects.state_kind import StateKind
from shell.infrastructure.platform.persistence.sql.mappers import (
    workflow_state_entity_to_model,
    workflow_state_model_to_entity,
)
from sqlalchemy import select

from ..models import WorkflowStateModel

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.workflow_state.value_objects.workflow_state_id import (
        WorkflowStateId,
    )
    from shell.domain.execution.aggregates.workflow_state.workflow_state import WorkflowState
    from sqlalchemy.ext.asyncio import AsyncSession


class SqlWorkflowStateRepository(WorkflowStateRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, id_: WorkflowStateId) -> WorkflowState | None:
        query = select(WorkflowStateModel).where(WorkflowStateModel.id == id_.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return workflow_state_model_to_entity(row) if row else None

    async def list_by_workflow_id(self, workflow_id: WorkflowId) -> list[WorkflowState]:
        query = select(WorkflowStateModel).where(WorkflowStateModel.workflow_id == workflow_id.value)
        rows = (await self._session.execute(query)).scalars().all()
        return [workflow_state_model_to_entity(row) for row in rows if row]

    async def list_by_workflow_id_and_kind(
        self, workflow_id: WorkflowId, kind: StateKind
    ) -> list[WorkflowState]:
        query = (
            select(WorkflowStateModel)
            .where(
                WorkflowStateModel.workflow_id == workflow_id.value,
                WorkflowStateModel.kind == kind.value,
            )
        )
        rows = (await self._session.execute(query)).scalars().all()
        return [workflow_state_model_to_entity(row) for row in rows if row]

    async def save(self, workflow_state: WorkflowState) -> None:
        model = await self._session.get(WorkflowStateModel, workflow_state.id.value)
        if model is None:
            model = workflow_state_entity_to_model(workflow_state)
            self._session.add(model)
        else:
            model.kind = workflow_state.kind.value
            model.payload = workflow_state.state_data.to_dict()
            model.is_current = True
            model.created_at = workflow_state.created_at.value

    async def delete(self, id_: WorkflowStateId) -> None:
        model = await self._session.get(WorkflowStateModel, id_.value)
        if model is not None:
            await self._session.delete(model)

    async def exists(self, id_: WorkflowStateId) -> bool:
        query = select(WorkflowStateModel).where(WorkflowStateModel.id == id_.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return row is not None
