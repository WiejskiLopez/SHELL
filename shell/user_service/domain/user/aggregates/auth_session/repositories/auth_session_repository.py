from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.platform.domain.value_objects.created_at import CreatedAt
    from shell.platform.domain.value_objects.exists_result import ExistsResult
    from shell.platform.domain.value_objects.hash import Hash
    from shell.user_service.domain.user.aggregates.auth_session.auth_session import AuthSession
    from shell.user_service.domain.user.aggregates.auth_session.value_objects.auth_session_id import (
        AuthSessionId,
    )
    from shell.user_service.domain.user.value_objects.user_id import UserId


class AuthSessionRepository(Protocol):
    async def save(self, auth_session: AuthSession) -> None: ...
    async def get_by_id(self, auth_session_id: AuthSessionId) -> AuthSession | None: ...
    async def get_by_token_hash(self, token_hash: Hash) -> AuthSession | None: ...
    async def get_active_by_user_id(
        self, user_id: UserId, now: CreatedAt
    ) -> AuthSession | None: ...
    async def delete(self, id: AuthSessionId) -> None: ...
    async def exists(self, id: AuthSessionId) -> ExistsResult: ...
