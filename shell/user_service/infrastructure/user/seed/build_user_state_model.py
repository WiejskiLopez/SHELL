from __future__ import annotations

from datetime import UTC, datetime

from shell.user_service.infrastructure.user.user_state.persistence.sql.models.user_state import (
    UserStateModel,
)


def build_user_state_model(
    *,
    state_id: str,
    user_id: str,
    direction: str,
    state_data: dict[str, object],
    created_at: datetime | None = None,
) -> UserStateModel:
    """Build a UserStateModel with deterministic values."""
    return UserStateModel(
        id=state_id,
        user_id=user_id,
        direction=direction,
        state_data=state_data,
        created_at=created_at or datetime.now(tz=UTC),
    )
