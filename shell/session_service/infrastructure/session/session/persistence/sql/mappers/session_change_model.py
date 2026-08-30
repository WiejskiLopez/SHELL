from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.session_service.domain.session.aggregates.session import Session
    from shell.session_service.infrastructure.session.session.persistence.sql.models.session import (
        SessionModel,
    )


def session_change_model(model: SessionModel, entity: Session) -> None:
    model.status = entity.session_status.value
    model.user_id = entity.user_id.value
    model.opened_at = entity.opened_at.value
    model.closed_at = entity.closed_at.value if entity.closed_at is not None else None
    model.changed_at = entity.changed_at.value
    model.deleted_at = entity.deleted_at.value if entity.deleted_at is not None else None
