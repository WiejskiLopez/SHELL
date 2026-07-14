"""SQL ORM model <-> domain entity mappers for UserState aggregate."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from shell.domain.user.aggregates.user_state.user_state import UserState
from shell.domain.user.aggregates.user_state.value_objects.user_state_id import UserStateId
from shell.domain.user.value_objects.user_id import UserId
from shell.infrastructure.user.user_state.persistence.sql.models.user_state import UserStateModel
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.state_data import StateData
from shell.platform.domain.value_objects.state_direction import StateDirection
from shell.platform.types import JsonStr  # noqa: TC001 -- potrzebny w runtime


def user_state_entity_to_model(entity: UserState) -> UserStateModel:
    return UserStateModel(
        id=entity.id.value,
        user_id=entity.user_id.value,
        direction=entity.direction.value,
        state_data=entity.snapshot(),
        created_at=entity.created_at.value if entity.created_at else None,
    )