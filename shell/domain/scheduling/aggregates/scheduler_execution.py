from __future__ import annotations

from datetime import datetime
from typing import Any

from shell.domain.platform.base import AggregateRoot
from shell.domain.scheduling.value_objects.ids import (
    SchedulerDefinitionId,
    SchedulerExecutionId,
)


class SchedulerExecution(AggregateRoot[SchedulerExecutionId]):
    """Represents a cyclic job configuration (not a one-shot execution)."""

    __slots__ = (
        "_scheduler_definition_id",
        "_name",
        "_job_type",
        "_interval_seconds",
        "_batch_size",
        "_enabled",
        "_config",
        "_created_at",
        "_updated_at",
    )

    def __init__(
        self,
        id: SchedulerExecutionId,
        scheduler_definition_id: SchedulerDefinitionId,
        name: str = "",
        job_type: str = "messaging",
        interval_seconds: float = 1.0,
        batch_size: int = 50,
        enabled: bool = True,
        config: dict[str, Any] | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        super().__init__(id)
        self._scheduler_definition_id = scheduler_definition_id
        self._name = name
        self._job_type = job_type
        self._interval_seconds = interval_seconds
        self._batch_size = batch_size
        self._enabled = enabled
        self._config = config or {}
        self._created_at = created_at or datetime.now()
        self._updated_at = updated_at or datetime.now()

    @property
    def scheduler_definition_id(self) -> SchedulerDefinitionId:
        return self._scheduler_definition_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def job_type(self) -> str:
        return self._job_type

    @property
    def interval_seconds(self) -> float:
        return self._interval_seconds

    @property
    def batch_size(self) -> int:
        return self._batch_size

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def config(self) -> dict[str, Any]:
        return dict(self._config)

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at
