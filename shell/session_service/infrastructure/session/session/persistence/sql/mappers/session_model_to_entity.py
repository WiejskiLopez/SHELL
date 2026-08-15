"""SQL ORM model <-> domain entity mappers for Session aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import DeletedAt
from shell.platform.domain.value_objects.updated_at import UpdatedAt
from shell.session_service.domain.session.aggregates.session import Session
from shell.session_service.domain.session.aggregates.session.value_objects.session_id import (
    SessionId,
)
from shell.session_service.domain.session.value_objects.session_status import SessionStatus
from shell.session_service.domain.session.value_objects.user_id_ref import UserIdRef

if TYPE_CHECKING:
    from shell.session_service.infrastructure.session.session.persistence.sql.models.session import (
        SessionModel,
    )


def session_model_to_entity(session_model: SessionModel) -> Session:
    return Session.restore(
        id=SessionId(session_model.id),
        user_id=UserIdRef(session_model.user_id),
        status=SessionStatus(session_model.status),
        opened_at=CreatedAt.from_datetime(session_model.opened_at),
        closed_at=UpdatedAt.from_datetime(session_model.closed_at),
        created_at=CreatedAt.from_datetime(session_model.created_at),
        updated_at=UpdatedAt.from_datetime(session_model.updated_at),
        deleted_at=DeletedAt.from_datetime(session_model.deleted_at),
    )
