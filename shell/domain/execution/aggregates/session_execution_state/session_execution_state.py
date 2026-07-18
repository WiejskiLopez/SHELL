from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.platform.domain.base import AggregateRoot

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.session_execution.value_objects.session_execution_id import (
        SessionExecutionId,
    )
    from shell.domain.execution.aggregates.session_execution_state.value_objects.session_execution_state_id import (
        SessionExecutionStateId,
    )
    from shell.platform.domain.value_objects.created_at import CreatedAt
    from shell.platform.domain.value_objects.state_data import StateData
    from shell.platform.domain.value_objects.state_direction import StateDirection

class SessionExecutionState(AggregateRoot["SessionExecutionStateId"]):
    __slots__ = (
        "_updated_at",
        "_session_execution_id",
        "_direction",
        "_state_data",
        "_created_at",
    )

    _session_execution_id: SessionExecutionId
    _direction: StateDirection
    _state_data: StateData
    _created_at: CreatedAt

    def __init__(
        self,
        id: SessionExecutionStateId,
        session_execution_id: SessionExecutionId,
        direction: StateDirection,
        state_data: StateData,
        created_at: CreatedAt,
    ) -> None:
        super().__init__(id)
        self._session_execution_id = session_execution_id
        self._direction = direction
        self._state_data = state_data
        self._created_at = created_at

    @classmethod
    def restore(
        cls,
        id: SessionExecutionStateId,
        session_execution_id: SessionExecutionId,
        direction: StateDirection,
        state_data: StateData,
        created_at: CreatedAt,
    ) -> Self:
        return cls(
            id=id,
            session_execution_id=session_execution_id,
            direction=direction,
            state_data=state_data,
            created_at=created_at,
        )

    def _delete(self) -> None:
        raise NotImplementedError("_delete() not yet implemented")

    @property
    def session_execution_id(self) -> SessionExecutionId:
        return self._session_execution_id

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
        id_: SessionExecutionStateId,
        session_execution_id: SessionExecutionId,
        state_data: StateData,
        now: CreatedAt,
        direction: StateDirection,
    ) -> SessionExecutionState:
        return cls(
            id=id_,
            session_execution_id=session_execution_id,
            direction=direction,
            state_data=state_data,
            created_at=now,
        )
