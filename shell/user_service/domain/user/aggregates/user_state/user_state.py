"""UserState — external input/output state for a user, a separate AggregateRoot.

Consolidates UserStateInput and UserStateOutput into a single aggregate
with a ``direction`` discriminator (StateDirection.IN or StateDirection.OUT).

INPUT state represents data fed into the user from external sources.
OUTPUT state represents data produced during user operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.platform.domain.base import AggregateRoot
from shell.platform.domain.exceptions.domain_error import DomainError
from shell.platform.domain.value_objects.changed_at import NONE_CHANGED_AT, ChangedAt
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import NONE_DELETED_AT, DeletedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.domain.value_objects.state_data import StateData
from shell.platform.types import JsonStr
from shell.user_service.domain.user.aggregates.user_state.events.user_state_changed_event import (
    UserStateChangedEvent,
)
from shell.user_service.domain.user.aggregates.user_state.events.user_state_created_event import (
    UserStateCreatedEvent,
)
from shell.user_service.domain.user.aggregates.user_state.events.user_state_deleted_event import (
    UserStateDeletedEvent,
)
from shell.user_service.domain.user.aggregates.user_state.value_objects.user_state_id import (
    UserStateId,
)

if TYPE_CHECKING:
    from shell.platform.domain.value_objects.state_direction import StateDirection
    from shell.user_service.domain.user.value_objects.user_id import UserId


class UserState(AggregateRoot[UserStateId]):
    __slots__ = (
        "_created_at",
        "_changed_at",
        "_deleted_at",
        "_user_id",
        "_direction",
        "_state_data",
    )

    _user_id: UserId
    _direction: StateDirection
    _state_data: StateData

    def __init__(
        self,
        *,
        id: UserStateId,
        created_at: CreatedAt,
        changed_at: ChangedAt = NONE_CHANGED_AT,
        deleted_at: DeletedAt = NONE_DELETED_AT,
        user_id: UserId,
        direction: StateDirection,
        state_data: StateData,
    ) -> None:
        super().__init__(id)
        self._user_id = user_id
        self._direction = direction
        self._state_data = state_data
        self._created_at = created_at
        self._changed_at = changed_at
        self._deleted_at = deleted_at

    @classmethod
    def create(
        cls,
        *,
        id_: UserStateId,
        now: CreatedAt,
        user_id: UserId,
        direction: StateDirection,
    ) -> UserState:
        return cls._new(
            id_=id_,
            user_id=user_id,
            direction=direction,
            now=OccurredAt.from_datetime(now.value),
        )

    # ------------------------------------------------------------------ mutations

    def change_state(self, state_data: StateData) -> None:
        if self._deleted_at.value is not None:
            raise DomainError("Cannot change state of a deleted user state")
        self._state_data = state_data
        self._change(now=OccurredAt.from_datetime(self._created_at.value))

    def snapshot(self) -> StateData:
        return self._state_data

    @classmethod
    def restore(
        cls,
        *,
        id: UserStateId,
        created_at: CreatedAt,
        changed_at: ChangedAt = NONE_CHANGED_AT,
        deleted_at: DeletedAt = NONE_DELETED_AT,
        user_id: UserId,
        direction: StateDirection,
        state_data: StateData,
    ) -> Self:
        return cls(
            id=id,
            user_id=user_id,
            direction=direction,
            state_data=state_data,
            created_at=created_at,
            changed_at=changed_at,
            deleted_at=deleted_at,
        )

    # ------------------------------------------------------------------ private transitions

    def _change(self, now: OccurredAt) -> None:
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            UserStateChangedEvent.now(
                user_id=self._user_id,
                user_state_id=self.id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            UserStateDeletedEvent.now(
                user_state_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

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
    def created_at(self) -> CreatedAt:
        return self._created_at

    @property
    def changed_at(self) -> ChangedAt:
        return self._changed_at

    @property
    def deleted_at(self) -> DeletedAt:
        return self._deleted_at

    # ------------------------------------------------------------------ factory

    @classmethod
    def _new(
        cls,
        *,
        id_: UserStateId,
        now: OccurredAt,
        user_id: UserId,
        direction: StateDirection,
    ) -> UserState:
        instance = cls(
            id=id_,
            user_id=user_id,
            direction=direction,
            state_data=StateData(JsonStr("{}")),
            created_at=CreatedAt.from_datetime(now.value),
        )
        instance.append_event(
            UserStateCreatedEvent.now(
                user_id=user_id,
                user_state_id=id_,
                now=OccurredAt.from_datetime(now.value),
            )
        )
        return instance
