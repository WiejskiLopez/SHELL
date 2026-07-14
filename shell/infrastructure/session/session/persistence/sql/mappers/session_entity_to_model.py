"""SQL ORM model <-> domain entity mappers for Session aggregate."""

from __future__ import annotations

from shell.domain.session.aggregates.session import Session
from shell.domain.session.aggregates.session.value_objects.session_id import SessionId
from shell.domain.session.value_objects.project_id_ref import ProjectIdRef
from shell.domain.session.value_objects.session_status import SessionStatus
from shell.domain.session.value_objects.user_id_ref import UserIdRef
from shell.infrastructure.session.session.persistence.sql.models.session import SessionModel
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.updated_at import UpdatedAt


def session_entity_to_model(session: Session) -> SessionModel:
    return SessionModel(
        id=session.id.value,
        goal=session.goal,
        status=session.status,
        user_id=session.user_id.value,
        project_id=session.project_id.value,
        created_at=session.opened_at.value,
        opened_at=session.opened_at.value,
        closed_at=session.closed_at.value if session.closed_at is not None else None,
    )

