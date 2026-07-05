"""TaskExecutionState — input/output payload for a TaskExecution, a separate AggregateRoot.

Consolidates TaskExecutionStateInput and TaskExecutionStateOutput into a single aggregate
with a ``direction`` discriminator (StateDirection.IN or StateDirection.OUT).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.platform.base import AggregateRoot
from shell.domain.platform.value_objects.state_data import StateData
from shell.domain.platform.value_objects.state_direction import StateDirection

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
        TaskExecutionId,
    )
    from shell.domain.execution.aggregates.task_execution_state.value_objects.task_execution_state_id import (
        TaskExecutionStateId,
    )
    from shell.domain.platform.value_objects.created_at import CreatedAt


class TaskExecutionState(AggregateRoot["TaskExecutionStateId"]):
    """Input or output payload for a TaskExecution, discriminated by kind."""

    __slots__ = (
        "_task_execution_id",
        "_direction",
        "_state_data",
        "_is_current",
        "_created_at",
    )

    _task_execution_id: TaskExecutionId
    _direction: StateDirection
    _state_data: StateData
    _is_current: bool
    _created_at: CreatedAt

    def __init__(
        self,
        id: TaskExecutionStateId,
        task_execution_id: TaskExecutionId,
        direction: StateDirection,
        is_current: bool,
        state_data: StateData | None = None,
        created_at: CreatedAt | None = None,
    ) -> None:
        super().__init__(id)
        self._task_execution_id = task_execution_id
        self._direction = direction
        self._state_data = state_data or StateData({})
        self._is_current = is_current
        if created_at is not None:
            self._created_at = created_at

    @classmethod
    def restore(
        cls,
        id: TaskExecutionStateId,
        task_execution_id: TaskExecutionId,
        direction: StateDirection,
        is_current: bool,
        state_data: StateData | None = None,
        created_at: CreatedAt | None = None,
    ) -> Self:
        return cls(
            id=id,
            task_execution_id=task_execution_id,
            direction=direction,
            state_data=state_data,
            is_current=is_current,
            created_at=created_at,
        )

    @property
    def task_execution_id(self) -> TaskExecutionId:
        return self._task_execution_id

    @property
    def direction(self) -> StateDirection:
        return self._direction

    @property
    def state_data(self) -> StateData:
        return self._state_data

    @property
    def is_current(self) -> bool:
        return self._is_current

    @property
    def created_at(self) -> CreatedAt:
        return self._created_at

    @classmethod
    def create(
        cls,
        *,
        id_: TaskExecutionStateId,
        task_execution_id: TaskExecutionId,
        direction: StateDirection = StateDirection.IN,
        state_data: StateData | None = None,
        now: CreatedAt,
    ) -> TaskExecutionState:
        return cls(
            id=id_,
            task_execution_id=task_execution_id,
            direction=direction,
            state_data=state_data or StateData({}),
            is_current=True,
            created_at=now,
        )

    def supersede(self) -> None:
        self._is_current = False
