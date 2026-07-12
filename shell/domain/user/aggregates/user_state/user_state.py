"""UserState — external input/output state for a user, a separate AggregateRoot.

Consolidates UserStateInput and UserStateOutput into a single aggregate
with a ``direction`` discriminator (StateDirection.IN or StateDirection.OUT).

INPUT state represents data fed into the user from external sources.
OUTPUT state represents data produced during user operations.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Self

from shell.domain.user.aggregates.user_state.events.user_state_changed_event import (
    UserStateChangedEvent,
)
from shell.domain.user.aggregates.user_state.value_objects.user_state_id import UserStateId
from shell.platform.domain.base import AggregateRoot
from shell.platform.domain.value_objects.state_data import StateData
from shell.platform.types import JsonStr

if TYPE_CHECKING:
    from shell.domain.user.value_objects.user_id import UserId
    from shell.platform.domain.value_objects.created_at import CreatedAt
    from shell.platform.domain.value_objects.deleted_at import DeletedAt
    from shell.platform.domain.value_objects.state_direction import StateDirection
    from shell.platform.domain.value_objects.updated_at import UpdatedAt


class UserState(AggregateRoot[UserStateId]):
    __slots__ = (
        "_user_id",
        "_direction",
        "_state_data",
        "_created_at",
        "_updated_at",
        "_deleted_at",
    )

    _user_id: UserId
    _direction: StateDirection
    _state_data: StateData

    def __init__(
        self,
        *,
        id: UserStateId,
        user_id: UserId,
        direction: StateDirection,
        state_data: StateData,
        created_at: CreatedAt,
        updated_at: UpdatedAt | None = None,
        deleted_at: DeletedAt | None = None,
    ) -> None:
        super().__init__(id)
        self._user_id = user_id
        self._direction = direction
        self._state_data = state_data
        self._created_at = created_at
        self._updated_at = updated_at
        self._deleted_at = deleted_at

    @classmethod
    def restore(
        cls,
        *,
        id: UserStateId,
        user_id: UserId,
        direction: StateDirection,
        state_data: StateData,
        created_at: CreatedAt,
        updated_at: UpdatedAt | None = None,
        deleted_at: DeletedAt | None = None,
    ) -> Self:
        return cls(
            id=id,
            user_id=user_id,
            direction=direction,
            state_data=state_data,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
        )

    # ------------------------------------------------------------------ properties

    @property
    def user_id(self) -> UserId:
        return self._user_id

    @property
    def direction(self) -> StateDirection:
        return self._direction

    @property
    def state_data(self) -> StateData:
        return self._state_data

    @property
    def created_at(self) -> CreatedAt | None:
        return self._created_at

    @property
    def updated_at(self) -> UpdatedAt | None:
        return self._updated_at

    @property
    def deleted_at(self) -> DeletedAt | None:
        return self._deleted_at

    # ------------------------------------------------------------------ factory

    @classmethod
    def create(
        cls,
        *,
        id_: UserStateId,
        user_id: UserId,
        direction: StateDirection,
        now: CreatedAt,
    ) -> UserState:
        return cls(
            id=id_,
            user_id=user_id,
            direction=direction,
            state_data=StateData(JsonStr("{}")),
            created_at=now,
        )

    # ------------------------------------------------------------------ mutations

    def set_key(self, key: str, value: object) -> None:
        old_value = json.loads(self._state_data.value.value).get(key)
        new_data = json.loads(self._state_data.value.value)
        new_data[key] = value
        self._state_data = StateData(JsonStr(json.dumps(new_data)))
        self.append_event(
            UserStateChangedEvent.now(
                user_id=self._user_id,
                user_state_id=self.id,
                direction=self._direction,
                key=key,
                old_value=old_value,
                new_value=value,
                now=self._created_at,
            )
        )

    def get(self, key: str) -> object | None:
        result: object | None = json.loads(self._state_data.value.value).get(key)
        return result

    def remove_key(self, key: str) -> None:
        if json.loads(self._state_data.value.value).get(key) is not None:
            old_value = json.loads(self._state_data.value.value).get(key)
            new_data = json.loads(self._state_data.value.value)
            new_data.pop(key, None)
            self._state_data = StateData(JsonStr(json.dumps(new_data)))
            self.append_event(
                UserStateChangedEvent.now(
                    user_id=self._user_id,
                    user_state_id=self.id,
                    direction=self._direction,
                    key=key,
                    old_value=old_value,
                    new_value=None,
                    now=self._created_at,
                )
            )

    def patch(self, data: JsonStr) -> None:
        parsed = json.loads(data.value)
        for key, value in parsed.items():
            self.set_key(key, value)

    def clear(self) -> None:
        current = json.loads(self._state_data.value.value)
        for key in list(current.keys()):
            self.remove_key(key)

    def merge(self, other: UserState) -> None:
        other_data = json.loads(other._state_data.value.value)
        current = json.loads(self._state_data.value.value)
        for key, value in other_data.items():
            if key not in current:
                self.set_key(key, value)

    def snapshot(self) -> StateData:
        return self._state_data

