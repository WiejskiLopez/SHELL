from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.user_execution_state import UserExecutionState
from shell.domain.execution.aggregates.user_execution_state.repositories.user_execution_state_repository import (
    UserExecutionStateRepository,
)
from shell.domain.execution.aggregates.user_execution_state.value_objects.user_execution_state_id import (
    UserExecutionStateId,
)
from shell.domain.platform.value_objects.exists_result import ExistsResult
from shell.infrastructure.platform.persistence.in_memory_repository import InMemoryRepository

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.user_execution.value_objects.user_execution_id import (
        UserExecutionId,
    )
    from shell.domain.platform.value_objects.state_direction import StateDirection


class InMemoryUserExecutionStateRepository(  # type: ignore[misc]
    InMemoryRepository[UserExecutionState, UserExecutionStateId], UserExecutionStateRepository
):
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
                if latest is None or item.created_at.value > latest.created_at.value:
                    latest = item
        return copy.deepcopy(latest) if latest is not None else None

    async def save(self, payload: UserExecutionState) -> None:
        existing = await self.get_latest_by_user_execution_id(
            payload.user_execution_id, direction=payload.direction
        )
        if existing is not None:
            existing.supersede()
        self._store[payload.id.value] = copy.deepcopy(payload)

    async def exists(self, id_: object) -> ExistsResult:
        return ExistsResult(id_.value in self._store)  # type: ignore[attr-defined]
