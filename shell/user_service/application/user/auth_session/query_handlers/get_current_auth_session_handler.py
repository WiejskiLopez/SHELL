from __future__ import annotations

from typing import TYPE_CHECKING

from shell.platform.domain.value_objects.hash import Hash

if TYPE_CHECKING:
    from shell.platform.domain.ports.time import Clock
    from shell.user_service.application.user.auth_session.dto.current_auth_session import (
        CurrentAuthSessionDto,
    )
    from shell.user_service.application.user.auth_session.ports.auth_session_query_service import (
        AuthSessionQueryService,
    )
    from shell.user_service.application.user.auth_session.queries.get_current_auth_session_query import (
        GetCurrentAuthSessionQuery,
    )


class GetCurrentAuthSessionHandler:
    def __init__(self, queries: AuthSessionQueryService, clock: Clock) -> None:
        self._queries = queries
        self._clock = clock

    async def handle(self, query: GetCurrentAuthSessionQuery) -> CurrentAuthSessionDto | None:
        if not query.token:
            return None

        return await self._queries.get_active_by_token_hash(
            token_hash=Hash.of(query.token).value,
            now=self._clock.now(),
        )
