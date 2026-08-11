"""SQL ORM model <-> domain entity mappers for Session aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.session.infrastructure.session.session.persistence.sql.models.session import SessionModel

if TYPE_CHECKING:
    from shell.session.domain.session.aggregates.session import Session


def session_entity_to_model(session: Session) -> SessionModel:
    return SessionModel(
        id=session.id.value,
        goal=session.goal,
        status=session._status.value,
        user_id=session.user_id.value,
        created_at=session.created_at.value,
        opened_at=session.opened_at.value,
        closed_at=session.closed_at.value if session.closed_at is not None else None,
        updated_at=session.updated_at.value,
        deleted_at=session.deleted_at.value if session._deleted_at is not None else None,
    )
