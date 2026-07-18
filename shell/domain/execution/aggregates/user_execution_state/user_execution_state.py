from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.platform.domain.base import AggregateRoot

from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.domain.execution.aggregates.user_execution_state.events.user_execution_state_created_event import UserExecutionStateCreatedEvent

from shell.platform.domain.value_objects.deleted_at import DeletedAt

from shell.platform.domain.value_objects.updated_at import UpdatedAt

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.user_execution.value_objects.user_execution_id import (
        UserExecutionId,
    )
    from shell.domain.execution.aggregates.user_execution_state.value_objects.user_execution_state_id import (
        UserExecutionStateId,
    )
    from shell.platform.domain.value_objects.created_at import CreatedAt
    from shell.platform.domain.value_objects.state_data import StateData
    from shell.platform.domain.value_objects.state_direction import StateDirection

class UserExecutionState(AggregateRoot["UserExecutionStateId"]):
    __slots__ = (
        "_updated_at",
        "_user_execution_id",
        "_direction",
        "_state_data",
        "_created_at",
    )

    _user_execution_id: UserExecutionId
    _direction: StateDirection
    _state_data: StateData
    _created_at: CreatedAt

    def __init__(
        self,
        id: UserExecutionStateId,
        user_execution_id: UserExecutionId,
        direction: StateDirection,
        state_data: StateData,
        created_at: CreatedAt,
    ) -> None:
        super().__init__(id)
        self._user_execution_id = user_execution_id
        self._direction = direction
        self._state_data = state_data
        self._created_at = created_at

    @classmethod
    def create(
        cls,
        *,
        id_: UserExecutionStateId,
        user_execution_id: UserExecutionId,
        state_data: StateData,
        now: CreatedAt,
        direction: StateDirection,
    ) -> UserExecutionState:
        return cls._new(id_=id_, user_execution_id=user_execution_id, state_data=state_data, now=now, direction=direction)

    @classmethod
    def restore(
        cls,
        id: UserExecutionStateId,
        user_execution_id: UserExecutionId,
        direction: StateDirection,
        state_data: StateData,
        created_at: CreatedAt,
    ) -> Self:
        return cls(
            id=id,
            user_execution_id=user_execution_id,
            direction=direction,
            state_data=state_data,
            created_at=created_at,
        )

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._updated_at = UpdatedAt.from_datetime(now.value)
        self.append_event(
            UserExecutionStateDeletedEvent.now(
                userexecutionstate_id=self._id,
                now=now,
            )
        )

    def _update(self, now: UpdatedAt) -> None:
        self._updated_at = now
        self.append_event(
            UserExecutionStateUpdatedEvent.now(
                userexecutionstate_id=self._id,
                now=now,
            )
        )

    @property
    def user_execution_id(self) -> UserExecutionId:
        return self._user_execution_id

    @property
    def direction(self) -> StateDirection:
        return self._direction

    @property
    def state_data(self) -> StateData:
        return self._state_data

    @property
    def created_at(self) -> CreatedAt:
        return self._created_at

    @classmethod
    def _new(
        cls,
        *,
        id_: UserExecutionStateId,
        user_execution_id: UserExecutionId,
        state_data: StateData,
        now: CreatedAt,
        direction: StateDirection,
    ) -> UserExecutionState:
        instance = cls(
            id=id_,
            user_execution_id=user_execution_id,
            direction=direction,
            state_data=state_data,
            created_at=now,
        )
        instance.append_event(
            UserExecutionStateCreatedEvent.now(
                userexecutionstate_id=instance.id,
                now=now,
            )
        )
        return instance