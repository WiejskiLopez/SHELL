from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.platform.value_objects.exists_result import ExistsResult
    from shell.domain.platform.value_objects.state_direction import StateDirection
    from shell.domain.project.aggregates.project_state.project_state import ProjectState
    from shell.domain.project.aggregates.project_state.value_objects.project_state_id import (
        ProjectStateId,
    )
    from shell.domain.project.value_objects.project_id import ProjectId


class ProjectStateRepository(Protocol):
    async def get_by_id(self, project_state_id: ProjectStateId) -> ProjectState | None: ...
    async def get_current_by_project_id_and_direction(
        self, project_id: ProjectId, direction: StateDirection
    ) -> ProjectState | None: ...
    async def save(self, state: ProjectState) -> None: ...
    async def delete(self, id: ProjectStateId) -> None: ...
    async def exists(self, id: ProjectStateId) -> ExistsResult: ...
