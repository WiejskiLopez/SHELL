from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from datetime import datetime

    from shell.user_service.application.user.auth_session.dto.current_auth_session import (
        CurrentAuthSessionDto,
    )


class AuthSessionQueryService(Protocol):
    async def get_active_by_token_hash(
        self,
        token_hash: str,
        now: datetime,
    ) -> CurrentAuthSessionDto | None: ...
