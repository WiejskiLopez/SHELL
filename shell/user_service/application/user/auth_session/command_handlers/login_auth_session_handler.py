from __future__ import annotations

from typing import TYPE_CHECKING

from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.hash import Hash
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.user_service.application.user.auth_session.dto.login_auth_session_result import (
    LoginAuthSessionResult,
)
from shell.user_service.domain.user.aggregates.auth_session.auth_session import AuthSession
from shell.user_service.domain.user.aggregates.auth_session.exceptions.auth_session_login_denied_error import (
    AuthSessionLoginDeniedError,
)
from shell.user_service.domain.user.aggregates.auth_session.repositories.auth_session_repository import (
    AuthSessionRepository,
)
from shell.user_service.domain.user.aggregates.auth_session.value_objects.auth_session_id import (
    AuthSessionId,
)
from shell.user_service.domain.user.aggregates.auth_session.value_objects.expires_at import (
    ExpiresAt,
)
from shell.user_service.domain.user.value_objects.user_email import UserEmail
from shell.user_service.domain.user.value_objects.user_status import UserStatus

if TYPE_CHECKING:
    from datetime import timedelta

    from shell.platform.application.ports.persistence.unit_of_work import UnitOfWork
    from shell.platform.domain.ports.identity import IdGenerator
    from shell.platform.domain.ports.time import Clock
    from shell.user_service.application.user.auth_session.commands.login_auth_session_command import (
        LoginAuthSessionCommand,
    )
    from shell.user_service.domain.user.aggregates.auth_session.ports.token_generator import (
        TokenGenerator,
    )
    from shell.user_service.domain.user.aggregates.auth_session.ports.user_query_provider import (
        UserQueryProvider,
    )


class LoginAuthSessionHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        user_query_provider: UserQueryProvider,
        clock: Clock,
        token_generator: TokenGenerator,
        id_generator: IdGenerator,
        session_ttl: timedelta,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._user_query_provider = user_query_provider
        self._clock = clock
        self._token_generator = token_generator
        self._id_generator = id_generator
        self._session_ttl = session_ttl

    async def handle(self, command: LoginAuthSessionCommand) -> LoginAuthSessionResult:
        raw_token = self._token_generator.generate()
        now = CreatedAt.from_datetime(self._clock.now())
        user_email = UserEmail(command.email)

        async with self._unit_of_work as unit_of_work:
            user_reference = await self._user_query_provider.get_by_email(user_email)
            if user_reference is None or user_reference.status != UserStatus.ACTIVE:
                raise AuthSessionLoginDeniedError()

            active_auth_session = await unit_of_work.repository(
                AuthSessionRepository
            ).get_active_by_user_id(user_reference.id, now)
            if active_auth_session is not None:
                active_auth_session.renew_token(
                    Hash.of(raw_token), OccurredAt.from_datetime(now.value)
                )
                auth_session = active_auth_session
            else:
                auth_session = AuthSession.create(
                    id_=self._id_generator.new_id(AuthSessionId),
                    now=now,
                    user_id=user_reference.id,
                    token_hash=Hash.of(raw_token),
                    expires_at=ExpiresAt.from_datetime(now.value + self._session_ttl),
                )

            # UoW.save() maps the aggregate's domain events to integration events
            # via the injected mapper and stages only those into the outbox.
            await unit_of_work.save(
                AuthSessionRepository,
                auth_session,
            )
            auth_session_id = auth_session.id.value

        return LoginAuthSessionResult(
            auth_session_id=auth_session_id,
            token=raw_token,
        )
