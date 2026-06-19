from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.platform.base import AggregateRoot

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.execution.value_objects.ids import (
    TaskExecutionId,
    TaskExecutionInputPayloadId
)


class TaskExecutionInputPayload(AggregateRoot["TaskExecutionInputPayloadId"]):
    """Input payload for a TaskExecution."""

    __slots__ = (
        "_task_execution_id",
        "_payload",
        "_is_current",
        "_created_at",
    )

    _task_execution_id: TaskExecutionId
    _payload: dict
    _is_current: bool
    _created_at: datetime

    def __init__(
        self,
        id: TaskExecutionInputPayloadId,
        task_execution_id: TaskExecutionId,
        payload: dict,
        is_current: bool,
        created_at: datetime,
    ) -> None:
        super().__init__(id)
        self._task_execution_id = task_execution_id
        self._payload = payload
        self._is_current = is_current
        self._created_at = created_at

    @property
    def task_execution_id(self) -> TaskExecutionId:
        return self._task_execution_id

    @property
    def payload(self) -> dict:
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
        id_: TaskExecutionInputPayloadId,
        task_execution_id: TaskExecutionId,
        payload: dict,
        now: datetime,
    ) -> TaskExecutionInputPayload:
        return cls(
            id=id_,
            task_execution_id=task_execution_id,
            payload=payload,
            is_current=True,
            created_at=now,
        )

    def supersede(self) -> None:
        self._is_current = False
