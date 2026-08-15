from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from shell.execution_service.domain.execution.aggregates.session_execution_state import (
    SessionExecutionState,
)
from shell.execution_service.domain.execution.aggregates.session_execution_state.repositories.session_execution_state_repository import (
    SessionExecutionStateRepository,
)
from shell.execution_service.domain.execution.aggregates.session_execution_state.value_objects.session_execution_state_id import (
    SessionExecutionStateId,
)
from shell.platform.domain.value_objects.exists_result import ExistsResult
from shell.platform.infrastructure.persistence.in_memory_repository import InMemoryRepository

if TYPE_CHECKING:
    from shell.execution_service.domain.execution.aggregates.session_execution.value_objects.session_execution_id import (
        SessionExecutionId,
    )
    from shell.platform.domain.value_objects.state_direction import StateDirection


class InMemorySessionExecutionStateRepository(  # type: ignore[misc]
    InMemoryRepository[SessionExecutionState, SessionExecutionStateId],
    SessionExecutionStateRepository,
):
    async def get_latest_by_session_execution_id(
        self,
        session_execution_id: SessionExecutionId,
        direction: StateDirection | None = None,
    ) -> SessionExecutionState | None:
        latest: SessionExecutionState | None = None
        for item in self._store.values():
            if item.session_execution_id == session_execution_id:
                if direction is not None and item.direction != direction:
                    continue
                if latest is None or item.created_at.value > latest.created_at.value:
                    latest = item
        return copy.deepcopy(latest) if latest is not None else None

    async def save(self, payload: SessionExecutionState) -> None:
        self._store[payload.id.value] = copy.deepcopy(payload)

    async def exists(self, id_: object) -> ExistsResult:
        key = id_.value if hasattr(id_, "value") else str(id_)
        return ExistsResult(key in self._store)
