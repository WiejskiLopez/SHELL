from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.domain.session.aggregates.session import Session
    from shell.infrastructure.session.session.persistence.sql.models.session import SessionModel


def session_update_model(model: SessionModel, entity: Session) -> None:
    model.goal = entity.goal
    model.status = entity._status
    model.user_id = entity.user_id.value
    model.project_id = entity.project_id.value
    model.opened_at = entity.opened_at.value
    model.closed_at = entity.closed_at.value if entity.closed_at is not None else None
    model.updated_at = entity.updated_at.value
    model.deleted_at = entity.deleted_at.value if entity.deleted_at is not None else None
