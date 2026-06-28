from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.user_execution.value_objects.user_execution_id import (
    UserExecutionId,
)
from shell.domain.execution.aggregates.user_execution_state.repositories.user_execution_state_repository import (
    UserExecutionStateRepository,
)
from shell.domain.execution.value_objects.state_direction import StateDirection

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.user_execution_state import UserExecutionState


class InMemoryUserExecutionStateRepository(UserExecutionStateRepository):
    def __init__(self) -> None:
        self._store: dict[str, UserExecutionState] = {}

    async def get_latest_by_user_execution_id(
        self,
        user_execution_id: UserExecutionId,
        direction: StateDirection | None = None,
    ) -> UserExecutionState | None:
        latest: UserExecutionState | None = None
        for item in self._store.values():
            if item.user_execution_id == user_execution_id:
                if direction is not None and item.direction != direction:
                    continue
                if latest is None or item.created_at > latest.created_at:
                    latest = item
        return copy.deepcopy(latest) if latest is not None else None

    async def save(self, payload: UserExecutionState) -> None:
        existing = await self.get_latest_by_user_execution_id(
            payload.user_execution_id, direction=payload.direction
        )
        if existing is not None:
            existing.supersede()
        self._store[payload.id.value] = copy.deepcopy(payload)

    async def delete(self, id_: object) -> None:
        self._store.pop(id_.value, None)

    async def exists(self, id_: object) -> bool:
        return id_.value in self._store
