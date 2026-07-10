from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.user.aggregates.user_state.user_state import UserState
    from shell.domain.user.aggregates.user_state.value_objects.user_state_id import UserStateId
    from shell.domain.user.value_objects.user_id import UserId
    from shell.platform.domain.value_objects.exists_result import ExistsResult
    from shell.platform.domain.value_objects.state_direction import StateDirection


class UserStateRepository(Protocol):
    async def get_by_id(self, user_state_id: UserStateId) -> UserState | None: ...
    async def get_current_by_user_id_and_direction(
        self, user_id: UserId, direction: StateDirection
    ) -> UserState | None: ...
    async def save(self, state: UserState) -> None: ...
    async def delete(self, id: UserStateId) -> None: ...
    async def exists(self, id: UserStateId) -> ExistsResult: ...
