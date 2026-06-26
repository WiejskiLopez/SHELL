"""TaskExecutionState — input/output payload for a TaskExecution, a separate AggregateRoot.

Consolidates TaskExecutionStateInput and TaskExecutionStateOutput into a single aggregate
with a ``kind`` discriminator (StateKind.INPUT or StateKind.OUTPUT).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.execution.value_objects.state_data import StateData
from shell.domain.execution.value_objects.state_kind import StateKind
from shell.domain.platform.base import AggregateRoot

from shell.domain.platform.value_objects.created_at import CreatedAt

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import TaskExecutionId
    from shell.domain.execution.aggregates.task_execution_state.value_objects.task_execution_state_id import (
        TaskExecutionStateId,
    )


class TaskExecutionState(AggregateRoot["TaskExecutionStateId"]):
    """Input or output payload for a TaskExecution, discriminated by kind."""

    __slots__ = (
        "_task_execution_id",
        "_kind",
        "_payload",
        "_is_current",
        "_created_at",
    )

    _task_execution_id: TaskExecutionId
    _kind: StateKind
    _payload: StateData
    _is_current: bool
    _created_at: CreatedAt

    def __init__(
        self,
        id: TaskExecutionStateId,
        task_execution_id: TaskExecutionId,
        kind: StateKind = StateKind.INPUT,
        payload: StateData | None = None,
        is_current: bool = True,
        created_at: CreatedAt | None = None,
    ) -> None:
        super().__init__(id)
        self._task_execution_id = task_execution_id
        self._kind = kind
        self._payload = payload or StateData({})
        self._is_current = is_current
        if created_at is not None:
            self._created_at = created_at

    @classmethod
    def restore(
        cls,
        id: TaskExecutionStateId,
        task_execution_id: TaskExecutionId,
        kind: StateKind = StateKind.INPUT,
        payload: StateData | None = None,
        is_current: bool = True,
        created_at: CreatedAt | None = None,
    ) -> Self:
        return cls(
            id=id,
            task_execution_id=task_execution_id,
            kind=kind,
            payload=payload,
            is_current=is_current,
            created_at=created_at,
        )

    @property
    def task_execution_id(self) -> TaskExecutionId:
        return self._task_execution_id

    @property
    def kind(self) -> StateKind:
        return self._kind

    @property
    def payload(self) -> StateData:
        return self._payload

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
        kind: StateKind = StateKind.INPUT,
        payload: StateData | None = None,
        now: CreatedAt,
    ) -> TaskExecutionState:
        return cls(
            id=id_,
            task_execution_id=task_execution_id,
            kind=kind,
            payload=payload or StateData({}),
            is_current=True,
            created_at=now,
        )

    def supersede(self) -> None:
        self._is_current = False
