from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.project.aggregates.project_state.project_state import ProjectState
from shell.domain.project.aggregates.project_state.repositories.project_state_repository import (
    ProjectStateRepository,
)
from shell.domain.project.aggregates.project_state.value_objects.project_state_id import (
    ProjectStateId,
)
from shell.infrastructure.platform.persistence.in_memory_repository import InMemoryRepository

if TYPE_CHECKING:
    from shell.domain.platform.value_objects.state_direction import StateDirection
    from shell.domain.project.value_objects.project_id import ProjectId


class InMemoryProjectStateRepository(
    InMemoryRepository[ProjectState, ProjectStateId], ProjectStateRepository
):
    async def get_current_by_project_id_and_direction(
        self, project_id: ProjectId, direction: StateDirection
    ) -> ProjectState | None:
        for state in self._store.values():
            if state.project_id == project_id and state.direction == direction:
                return state
        return None
