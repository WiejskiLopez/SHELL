"""SQL ORM model <-> domain entity mappers for UserState aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.infrastructure.user.user_state.persistence.sql.models.user_state import UserStateModel

if TYPE_CHECKING:
    from shell.domain.user.aggregates.user_state.user_state import UserState


def user_state_entity_to_model(entity: UserState) -> UserStateModel:
    return UserStateModel(
        id=entity.id.value,
        user_id=entity.user_id.value,
        direction=entity.direction.value,
        state_data=entity.snapshot(),
        created_at=entity.created_at.value if entity.created_at else None,
    )