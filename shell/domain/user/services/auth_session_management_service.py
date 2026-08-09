from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.user.aggregates.auth_session.auth_session import AuthSession
from shell.domain.user.aggregates.auth_session.events.auth_session_login_failed_event import (
    AuthSessionLoginFailedEvent,
)
from shell.domain.user.aggregates.auth_session.events.auth_session_login_succeeded_event import (
    AuthSessionLoginSucceededEvent,
)
from shell.domain.user.aggregates.auth_session.value_objects.auth_session_id import (
    AuthSessionId,
)
from shell.domain.user.services.auth_session_login_outcome import AuthSessionLoginOutcome
from shell.domain.user.value_objects.user_status import UserStatus
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.domain.value_objects.updated_at import UpdatedAt

if TYPE_CHECKING:
    from datetime import timedelta

    from shell.domain.user.aggregates.user.user import User
    from shell.domain.user.value_objects.user_email import UserEmail
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
        user_email: UserEmail,
        active_auth_session: AuthSession | None,
        now: CreatedAt,
        token_hash: Hash,
    ) -> AuthSessionLoginOutcome:
        occurred_at = OccurredAt.from_datetime(now.value)
        if user is None or user.status != UserStatus.ACTIVE:
            return AuthSessionLoginOutcome(
                auth_session=None,
                domain_events=(
                    AuthSessionLoginFailedEvent.now(
                        now=occurred_at,
                    ),
                ),
            )
        if active_auth_session is not None:
            active_auth_session.renew_token(token_hash, UpdatedAt.from_datetime(now.value))
            return AuthSessionLoginOutcome(
                auth_session=active_auth_session,
                domain_events=(
                    AuthSessionLoginSucceededEvent.now(
                        auth_session_id=active_auth_session.id,
                        user_id=user.id,
                        now=occurred_at,
                    ),
                ),
            )
        expires_at = CreatedAt.from_datetime(now.value + self._session_ttl_)
        auth_session = AuthSession.create(
            id_=self._id_generator_.new_id(AuthSessionId),
            now=now,
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        return AuthSessionLoginOutcome(
            auth_session=auth_session,
            domain_events=(
                AuthSessionLoginSucceededEvent.now(
                    auth_session_id=auth_session.id,
                    user_id=user.id,
                    now=occurred_at,
                ),
            ),
        )
