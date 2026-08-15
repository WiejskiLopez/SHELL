from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.user_service.application.user.user_state.dto.user_state import UserStateDto


class UserStateQueryService(Protocol):
    async def get_by_id(self, user_state_id: str) -> UserStateDto | None: ...
