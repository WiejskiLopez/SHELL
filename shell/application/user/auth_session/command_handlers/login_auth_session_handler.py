from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.user.auth_session.dto.login_auth_session_result import (
    LoginAuthSessionResult,
)
from shell.domain.user.aggregates.auth_session.exceptions.auth_session_login_denied_error import (
    AuthSessionLoginDeniedError,
)
from shell.domain.user.aggregates.auth_session.repositories.auth_session_repository import (
    AuthSessionRepository,
)
from shell.domain.user.value_objects.user_email import UserEmail
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.hash import Hash

if TYPE_CHECKING:
    from shell.application.user.auth_session.commands.login_auth_session_command import (
        LoginAuthSessionCommand,
    )
    from shell.domain.user.aggregates.auth_session.auth_session import AuthSession
    from shell.domain.user.aggregates.auth_session.ports.token_generator import (
        TokenGenerator,
    )
    from shell.domain.user.aggregates.auth_session.ports.user_query_provider import (
        UserQueryProvider,
    )
    from shell.domain.user.services.auth_session_management_service import (
        AuthSessionManagementService,
    )
    from shell.platform.application.ports.unit_of_work import UnitOfWork
    from shell.platform.domain.ports.time import Clock


class LoginAuthSessionHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        user_query_provider: UserQueryProvider,
        clock: Clock,
        token_generator: TokenGenerator,
        auth_session_service: AuthSessionManagementService,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._user_query_provider = user_query_provider
        self._clock = clock
        self._token_generator = token_generator
        self._auth_session_service = auth_session_service

    async def handle(self, command: LoginAuthSessionCommand) -> LoginAuthSessionResult:
        raw_token = self._token_generator.generate()
        now = CreatedAt.from_datetime(self._clock.now())
        user_email = UserEmail(command.email)

        async with self._unit_of_work as unit_of_work:
            user = await self._user_query_provider.get_by_email(user_email)

            active_auth_session: AuthSession | None = None
            if user is not None:
                active_auth_session = await unit_of_work.repository(
                    AuthSessionRepository
                ).get_active_by_user_id(user.id, now)

            outcome = self._auth_session_service.ensure_login(
                user=user,
                user_email=user_email,
                active_auth_session=active_auth_session,
                now=now,
                token_hash=Hash.of(raw_token),
            )

            unit_of_work.stage_events(outcome.domain_events)

            if outcome.auth_session is not None:
                await unit_of_work.save(AuthSessionRepository, outcome.auth_session)
                auth_session_id = outcome.auth_session.id.value
            else:
                auth_session_id = None

        if auth_session_id is None:
            raise AuthSessionLoginDeniedError()

        return LoginAuthSessionResult(
            auth_session_id=auth_session_id,
            token=raw_token,
        )
