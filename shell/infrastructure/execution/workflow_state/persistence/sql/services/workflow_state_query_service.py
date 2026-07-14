from __future__ import annotations

import json
from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.application.execution.workflow.dto.workflow_state import WorkflowStateDto
from shell.infrastructure.execution.workflow_state.persistence.sql.models.workflow_state import (
    WorkflowStateModel,
)
from shell.platform.types import JsonStr

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class WorkflowStateQueryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, workflow_state_id: str) -> WorkflowStateDto | None:
        async with self._session_factory() as session:
            stmt = select(WorkflowStateModel).where(WorkflowStateModel.id == workflow_state_id)
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return None
            return WorkflowStateDto(
                id=model.id,
                workflow_id=model.workflow_id,
                direction=model.direction,
                state_data=JsonStr(json.dumps(dict(model.state_data))),
                created_at=model.created_at,
            )
