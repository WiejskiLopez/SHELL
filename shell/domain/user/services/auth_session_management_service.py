from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.user.aggregates.auth_session.auth_session import AuthSession
from shell.domain.user.aggregates.auth_session.exceptions.auth_session_login_denied_error import (
    AuthSessionLoginDeniedError,
)
from shell.domain.user.aggregates.auth_session.value_objects.auth_session_id import (
    AuthSessionId,
)
from shell.domain.user.value_objects.user_status import UserStatus
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.updated_at import UpdatedAt

if TYPE_CHECKING:
    from datetime import timedelta

    from shell.domain.user.aggregates.user.user import User
    from shell.platform.domain.ports.identity import IdGenerator
    from shell.platform.domain.value_objects.hash import Hash


class AuthSessionManagementService:
    def __init__(self, id_generator: IdGenerator, session_ttl: timedelta) -> None:
        self._id_generator_ = id_generator
        self._session_ttl_ = session_ttl

    def ensure_login(
        self,
        *,
        user: User | None,
        active_auth_session: AuthSession | None,
        now: CreatedAt,
        token_hash: Hash,
    ) -> AuthSession:
        if user is None or user.status != UserStatus.ACTIVE:
            raise AuthSessionLoginDeniedError()
        if active_auth_session is not None:
            active_auth_session.renew_token(token_hash, UpdatedAt.from_datetime(now.value))
            return active_auth_session
        expires_at = CreatedAt.from_datetime(now.value + self._session_ttl_)
        return AuthSession.create(
            id_=self._id_generator_.new_id(AuthSessionId),
            now=now,
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
