"""Builders producing Session BC ORM model instances for seeding and tests."""

from __future__ import annotations

from datetime import UTC, datetime

from shell.session_service.infrastructure.session.session.persistence.sql.models.session import (
    SessionModel,
)
from shell.session_service.infrastructure.session.session_state.persistence.sql.models.session_state import (
    SessionStateModel,
)


def build_session_model(
    *,
    session_id: str,
    user_id: str,
    status: str,
    opened_at: datetime | None = None,
    closed_at: datetime | None = None,
    created_at: datetime | None = None,
) -> SessionModel:
    """Build a SessionModel with deterministic values."""
    now = created_at or datetime.now(tz=UTC)
    return SessionModel(
        id=session_id,
        user_id=user_id,
        status=status,
        created_at=now,
        opened_at=opened_at or now,
        closed_at=closed_at,
    )


def build_session_state_model(
    *,
    state_id: str,
    session_id: str,
    direction: str,
    state_data: dict[str, object],
    created_at: datetime | None = None,
) -> SessionStateModel:
    """Build a SessionStateModel with deterministic values."""
    return SessionStateModel(
        id=state_id,
        session_id=session_id,
        direction=direction,
        state_data=state_data,
        created_at=created_at or datetime.now(tz=UTC),
    )


__all__ = [
    "build_session_model",
    "build_session_state_model",
]
