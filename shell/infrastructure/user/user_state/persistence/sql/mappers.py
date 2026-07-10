"""SQL ORM model <-> domain entity mappers for UserState aggregate."""

from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.user.aggregates.user_state.user_state import UserState
from shell.domain.user.aggregates.user_state.value_objects.user_state_id import UserStateId
from shell.domain.user.value_objects.user_id import UserId
from shell.infrastructure.user.user_state.persistence.sql.models.user_state import UserStateModel
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.state_data import StateData
from shell.platform.domain.value_objects.state_direction import StateDirection


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def user_state_model_to_entity(model: UserStateModel) -> UserState:
    return UserState.restore(
        id=UserStateId(model.id),
        user_id=UserId(model.user_id),
        direction=StateDirection(model.direction),
        state_data=StateData(dict(model.state_data)) if model.state_data else StateData({}),
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),
    )


def user_state_entity_to_model(entity: UserState) -> UserStateModel:
    return UserStateModel(
        id=entity.id.value,
        user_id=entity.user_id.value,
        direction=entity.direction.value,
        state_data=entity.snapshot(),
        created_at=entity.created_at.value if entity.created_at else None,
    )
