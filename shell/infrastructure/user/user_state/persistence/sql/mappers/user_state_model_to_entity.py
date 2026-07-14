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


def user_state_model_to_entity(model: UserStateModel) -> UserState:
    return UserState.restore(
        id=UserStateId(model.id),
        user_id=UserId(model.user_id),
        direction=StateDirection(model.direction),
        state_data=StateData(JsonStr(json.dumps(dict(model.state_data)))) if model.state_data else StateData(JsonStr("{}")),
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),
    )

