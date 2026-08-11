from __future__ import annotations

from typing import TYPE_CHECKING

from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.updated_at import UpdatedAt
from shell.session.domain.session.aggregates.session import Session
from shell.session.domain.session.aggregates.session.value_objects.session_id import SessionId

if TYPE_CHECKING:
    from datetime import datetime

    from shell.platform.domain.ports.identity import IdGenerator
    from shell.session.domain.session.value_objects.user_id_ref import UserIdRef


class SessionManagementService:
    def __init__(self, id_generator: IdGenerator) -> None:
        self._id_generator_ = id_generator

    def ensure_open(
        self,
        *,
        user_id_ref: UserIdRef,
        now_dt: datetime,
        existing: Session | None,
    ) -> Session:
        if existing is not None:
            existing.update(UpdatedAt.from_datetime(now_dt))
            return existing
        session_id = self._id_generator_.new_id(SessionId)
        return Session.open(
            id_=session_id,
            user_id=user_id_ref,
            now=CreatedAt.from_datetime(now_dt),
        )
