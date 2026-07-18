"""TaskExecutionState — input/output payload for a TaskExecution, a separate AggregateRoot.

Consolidates TaskExecutionStateInput and TaskExecutionStateOutput into a single aggregate
with a ``direction`` discriminator (StateDirection.IN or StateDirection.OUT).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.platform.domain.base import AggregateRoot

from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.domain.execution.aggregates.task_execution_state.events.task_execution_state_created_event import TaskExecutionStateCreatedEvent

from shell.platform.domain.value_objects.deleted_at import DeletedAt

from shell.platform.domain.value_objects.updated_at import UpdatedAt

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
        TaskExecutionId,
    )
    from shell.domain.execution.aggregates.task_execution_state.value_objects.task_execution_state_id import (
        TaskExecutionStateId,
    )
    from shell.platform.domain.value_objects.created_at import CreatedAt
    from shell.platform.domain.value_objects.state_data import StateData
    from shell.platform.domain.value_objects.state_direction import StateDirection

class TaskExecutionState(AggregateRoot["TaskExecutionStateId"]):
    """Input or output payload for a TaskExecution, discriminated by kind."""

    __slots__ = (
        "_updated_at",
        "_task_execution_id",
        "_direction",
        "_state_data",
        "_created_at",
    )

    _task_execution_id: TaskExecutionId
    _direction: StateDirection
    _state_data: StateData
    _created_at: CreatedAt

    def __init__(
        self,
        id: TaskExecutionStateId,
        task_execution_id: TaskExecutionId,
        direction: StateDirection,
        state_data: StateData,
        created_at: CreatedAt,
    ) -> None:
        super().__init__(id)
        self._task_execution_id = task_execution_id
        self._direction = direction
        self._state_data = state_data
        self._created_at = created_at

    @classmethod
    def create(
        cls,
        *,
        id_: TaskExecutionStateId,
        task_execution_id: TaskExecutionId,
        state_data: StateData,
        now: CreatedAt,
        direction: StateDirection,
    ) -> TaskExecutionState:
        return cls._new(id_=id_, task_execution_id=task_execution_id, state_data=state_data, now=now, direction=direction)

    @classmethod
    def restore(
        cls,
        id: TaskExecutionStateId,
        task_execution_id: TaskExecutionId,
        direction: StateDirection,
        state_data: StateData,
        created_at: CreatedAt,
    ) -> Self:
        return cls(
            id=id,
            task_execution_id=task_execution_id,
            direction=direction,
            state_data=state_data,
            created_at=created_at,
        )

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._updated_at = UpdatedAt.from_datetime(now.value)
        self.append_event(
            TaskExecutionStateDeletedEvent.now(
                taskexecutionstate_id=self._id,
                now=now,
            )
        )

    def _update(self, now: UpdatedAt) -> None:
        self._updated_at = now
        self.append_event(
            TaskExecutionStateUpdatedEvent.now(
                taskexecutionstate_id=self._id,
                now=now,
            )
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
    def created_at(self) -> CreatedAt:
        return self._created_at

    @classmethod
    def _new(
        cls,
        *,
        id_: TaskExecutionStateId,
        task_execution_id: TaskExecutionId,
        state_data: StateData,
        now: CreatedAt,
        direction: StateDirection,
    ) -> TaskExecutionState:
        instance = cls(
            id=id_,
            task_execution_id=task_execution_id,
            direction=direction,
            state_data=state_data,
            created_at=now,
        )
        instance.append_event(
            TaskExecutionStateCreatedEvent.now(
                taskexecutionstate_id=instance.id,
                now=now,
            )
        )
        return instance