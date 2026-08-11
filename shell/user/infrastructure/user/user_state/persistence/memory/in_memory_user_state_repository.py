from __future__ import annotations

from typing import TYPE_CHECKING

from shell.platform.infrastructure.persistence.in_memory_repository import InMemoryRepository
from shell.user.domain.user.aggregates.user_state.repositories.user_state_repository import (
    UserStateRepository,
)
from shell.user.domain.user.aggregates.user_state.user_state import UserState
from shell.user.domain.user.aggregates.user_state.value_objects.user_state_id import UserStateId

if TYPE_CHECKING:
    from shell.platform.domain.value_objects.state_direction import StateDirection
    from shell.user.domain.user.value_objects.user_id import UserId


class InMemoryUserStateRepository(InMemoryRepository[UserState, UserStateId], UserStateRepository):
    async def get_current_by_user_id_and_direction(
        self, user_id: UserId, direction: StateDirection
    ) -> UserState | None:
        for state in self._store.values():
            if state.user_id == user_id and state.direction == direction:
                return state
        return None
