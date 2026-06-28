from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.session_execution.value_objects.session_execution_id import (
    SessionExecutionId,
)
from shell.domain.execution.aggregates.session_execution_state.repositories.session_execution_state_repository import (
    SessionExecutionStateRepository,
)
from shell.domain.execution.value_objects.state_direction import StateDirection

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.session_execution_state import SessionExecutionState


class InMemorySessionExecutionStateRepository(SessionExecutionStateRepository):
    def __init__(self) -> None:
        self._store: dict[str, SessionExecutionState] = {}

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
                if latest is None or item.created_at > latest.created_at:
                    latest = item
        return copy.deepcopy(latest) if latest is not None else None

    async def save(self, payload: SessionExecutionState) -> None:
        existing = await self.get_latest_by_session_execution_id(
            payload.session_execution_id, direction=payload.direction
        )
        if existing is not None:
            existing.supersede()
        self._store[payload.id.value] = copy.deepcopy(payload)

    async def delete(self, id_: object) -> None:
        self._store.pop(id_.value, None)

    async def exists(self, id_: object) -> bool:
        return id_.value in self._store
