from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.platform.domain.value_objects.occurred_at import OccurredAt
    from shell.user_service.domain.user.aggregates.auth_session.value_objects.auth_session_id import (
        AuthSessionId,
    )
    from shell.user_service.domain.user.value_objects.user_id import UserId


@dataclass(frozen=True, slots=True, kw_only=True)
class AuthSessionDeletedEvent(DomainEvent):
    auth_session_id: AuthSessionId
    user_id: UserId

    @classmethod
    def now(
        cls,
        *,
        auth_session_id: AuthSessionId,
        user_id: UserId,
        now: OccurredAt,
    ) -> AuthSessionDeletedEvent:
        return cls(
            occurred_at=now,
            auth_session_id=auth_session_id,
            user_id=user_id,
        )
