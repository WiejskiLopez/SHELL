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


def session_update_model(model: SessionModel, entity: Session) -> None:
    model.goal = entity.goal
    model.status = entity.status
    model.user_id = entity.user_id.value
    model.project_id = entity.project_id.value
    model.opened_at = entity.opened_at.value
    model.closed_at = entity.closed_at.value if entity.closed_at is not None else None