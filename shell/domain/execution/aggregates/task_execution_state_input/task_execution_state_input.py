from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

from shell.domain.platform.base import AggregateRoot

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import TaskExecutionId
    from shell.domain.execution.aggregates.task_execution_state_input.value_objects.task_execution_state_input_id import (
        TaskExecutionStateInputId,
    )


class TaskExecutionStateInput(AggregateRoot["TaskExecutionStateInputId"]):
    """Input payload for a TaskExecution."""

    __slots__ = (
        "_task_execution_id",
        "_payload",
        "_is_current",
        "_created_at",
    )

    _task_execution_id: TaskExecutionId
    _payload: dict[str, Any]
    _is_current: bool
    _created_at: datetime

    def __init__(
        self,
        id: TaskExecutionStateInputId,
        task_execution_id: TaskExecutionId,
        payload: dict[str, Any],
        is_current: bool,
        created_at: datetime,
    ) -> None:
        super().__init__(id)
        self._task_execution_id = task_execution_id
        self._payload = payload
        self._is_current = is_current
        self._created_at = created_at

    @classmethod
    def restore(
        cls,
        id: TaskExecutionStateInputId,
        task_execution_id: TaskExecutionId,
        payload: dict[str, Any],
        is_current: bool,
        created_at: datetime,
    ) -> Self:
        return cls(
            id=id,
            task_execution_id=task_execution_id,
            payload=payload,
            is_current=is_current,
            created_at=created_at,
        )

    @property
    def task_execution_id(self) -> TaskExecutionId:
        return self._task_execution_id

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
        id_: TaskExecutionStateInputId,
        task_execution_id: TaskExecutionId,
        payload: dict[str, Any],
        now: datetime,
    ) -> TaskExecutionStateInput:
        return cls(
            id=id_,
            task_execution_id=task_execution_id,
            payload=payload,
            is_current=True,
            created_at=now,
        )

    def supersede(self) -> None:
        self._is_current = False
