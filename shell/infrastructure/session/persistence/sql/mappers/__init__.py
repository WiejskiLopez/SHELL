"""SQL ORM model <-> domain entity mappers for Session BC."""

from __future__ import annotations

from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.updated_at import UpdatedAt
from shell.domain.session.aggregates.session import Session
from shell.domain.session.aggregates.session.value_objects.session_id import SessionId
from shell.domain.session.value_objects.project_id_ref import ProjectIdRef
from shell.domain.session.value_objects.session_status import SessionStatus
from shell.domain.session.value_objects.user_id_ref import UserIdRef
from shell.infrastructure.session.persistence.sql.models import SessionModel


def session_model_to_entity(session_model: SessionModel) -> Session:
    return Session(
        id=SessionId(session_model.id),
        user_id=UserIdRef(session_model.user_id),
        project_id=ProjectIdRef(session_model.project_id),
        status=SessionStatus(session_model.status),
        opened_at=CreatedAt.from_datetime(session_model.opened_at),
        closed_at=UpdatedAt.from_datetime(session_model.closed_at)
        if session_model.closed_at
        else None,
    )


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


def session_update_model(model: SessionModel, entity: Session) -> None:
    model.goal = entity.goal
    model.status = entity.status
    model.user_id = entity.user_id.value
    model.project_id = entity.project_id.value
    model.opened_at = entity.opened_at.value
    model.closed_at = entity.closed_at.value if entity.closed_at is not None else None
