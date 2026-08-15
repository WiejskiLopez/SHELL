from __future__ import annotations

from typing import TYPE_CHECKING

from shell.platform.infrastructure.persistence.in_memory_repository import InMemoryRepository
from shell.user_service.domain.user.aggregates.auth_session.auth_session import AuthSession
from shell.user_service.domain.user.aggregates.auth_session.repositories.auth_session_repository import (
    AuthSessionRepository,
)
from shell.user_service.domain.user.aggregates.auth_session.value_objects.auth_session_id import (
    AuthSessionId,
)

if TYPE_CHECKING:
    from shell.platform.domain.value_objects.created_at import CreatedAt
    from shell.platform.domain.value_objects.hash import Hash
    from shell.user_service.domain.user.value_objects.user_id import UserId


class InMemoryAuthSessionRepository(
    InMemoryRepository[AuthSession, AuthSessionId],
    AuthSessionRepository,
):
    async def get_by_token_hash(self, token_hash: Hash) -> AuthSession | None:
        for auth_session in self._store.values():
            if auth_session.token_hash == token_hash:
                return auth_session
        return None

    async def get_active_by_user_id(self, user_id: UserId, now: CreatedAt) -> AuthSession | None:
        active: AuthSession | None = None
        for auth_session in self._store.values():
            if (
                auth_session.user_id == user_id
                and auth_session.revoked_at.value is None
                and auth_session.deleted_at.value is None
                and auth_session.expires_at.value > now.value
                and (active is None or auth_session.created_at.value > active.created_at.value)
            ):
                active = auth_session
        return active
