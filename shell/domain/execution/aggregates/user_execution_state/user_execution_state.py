from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.platform.domain.base import AggregateRoot

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

    def _delete(self) -> None:
        raise NotImplementedError("_delete() not yet implemented")

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
    def create(
        cls,
        *,
        id_: UserExecutionStateId,
        user_execution_id: UserExecutionId,
        state_data: StateData,
        now: CreatedAt,
        direction: StateDirection,
    ) -> UserExecutionState:
        return cls(
            id=id_,
            user_execution_id=user_execution_id,
            direction=direction,
            state_data=state_data,
            created_at=now,
        )
