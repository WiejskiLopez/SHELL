"""TaskExecutionState — input/output payload for a TaskExecution, a separate AggregateRoot.

Consolidates TaskExecutionStateInput and TaskExecutionStateOutput into a single aggregate
with a ``kind`` discriminator (StateKind.INPUT or StateKind.OUTPUT).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

from shell.domain.execution.value_objects.state_kind import StateKind
from shell.domain.platform.base import AggregateRoot

if TYPE_CHECKING:
    from datetime import datetime

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
    _payload: dict[str, Any]
    _is_current: bool
    _created_at: datetime

    def __init__(
        self,
        id: TaskExecutionStateId,
        task_execution_id: TaskExecutionId,
        kind: StateKind = StateKind.INPUT,
        payload: dict[str, Any] | None = None,
        is_current: bool = True,
        created_at: datetime | None = None,
    ) -> None:
        super().__init__(id)
        self._task_execution_id = task_execution_id
        self._kind = kind
        self._payload = payload or {}
        self._is_current = is_current
        if created_at is not None:
            self._created_at = created_at

    @classmethod
    def restore(
        cls,
        id: TaskExecutionStateId,
        task_execution_id: TaskExecutionId,
        kind: StateKind = StateKind.INPUT,
        payload: dict[str, Any] | None = None,
        is_current: bool = True,
        created_at: datetime | None = None,
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
    def payload(self) -> dict[str, Any]:
        return self._payload

    @property
    def is_current(self) -> bool:
        return self._is_current

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @classmethod
    def create(
        cls,
        *,
        id_: TaskExecutionStateId,
        task_execution_id: TaskExecutionId,
        kind: StateKind = StateKind.INPUT,
        payload: dict[str, Any] | None = None,
        now: datetime,
    ) -> TaskExecutionState:
        return cls(
            id=id_,
            task_execution_id=task_execution_id,
            kind=kind,
            payload=payload or {},
            is_current=True,
            created_at=now,
        )

    def supersede(self) -> None:
        self._is_current = False
