from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.domain.project.aggregates.project_state.repositories.project_state_repository import (
    ProjectStateRepository,
)
from shell.infrastructure.project.project_state.persistence.sql.mappers import (
    project_state_entity_to_model,
    project_state_model_to_entity,
)
from shell.platform.domain.value_objects.exists_result import ExistsResult

from ..models import ProjectStateModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.domain.project.aggregates.project.value_objects.project_id import ProjectId
    from shell.domain.project.aggregates.project_state.project_state import ProjectState
    from shell.domain.project.aggregates.project_state.value_objects.project_state_id import (
        ProjectStateId,
    )
    from shell.platform.domain.value_objects.state_direction import StateDirection


class SqlProjectStateRepository(ProjectStateRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, project_state_id: ProjectStateId) -> ProjectState | None:
        query = select(ProjectStateModel).where(ProjectStateModel.id == project_state_id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return project_state_model_to_entity(row) if row else None

    async def get_current_by_project_id_and_direction(
        self, project_id: ProjectId, direction: StateDirection
    ) -> ProjectState | None:
        query = select(ProjectStateModel).where(
            ProjectStateModel.project_id == project_id.value,
            ProjectStateModel.direction == direction.value,
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        return project_state_model_to_entity(row) if row else None

    async def save(self, state: ProjectState) -> None:
        model = await self._session.get(ProjectStateModel, state.id.value)
        if model is None:
            existing = await self.get_current_by_project_id_and_direction(
                state.project_id, state.direction
            )
            if existing is not None:
                old_model = await self._session.get(ProjectStateModel, existing.id.value)
                if old_model is not None:
                    await self._session.delete(old_model)
            model = project_state_entity_to_model(state)
            self._session.add(model)
        else:
            model.direction = state.direction.value
            model.state_data = state.snapshot()  # type: ignore[assignment]
            model.updated_at = state.updated_at.value

    async def delete(self, id: ProjectStateId) -> None:
        model = await self._session.get(ProjectStateModel, id.value)
        if model is not None:
            await self._session.delete(model)

    async def exists(self, id: ProjectStateId) -> ExistsResult:
        query = select(ProjectStateModel).where(ProjectStateModel.id == id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return ExistsResult(row is not None)
