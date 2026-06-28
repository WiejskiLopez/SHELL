from __future__ import annotations

from typing import Any, Self

from shell.domain.execution.value_objects.state_data import StateData
from shell.domain.platform.base import AggregateRoot
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.enabled import Enabled
from shell.domain.platform.value_objects.timestamp import Timestamp
from shell.domain.scheduling.value_objects.batch_size import BatchSize
from shell.domain.scheduling.value_objects.ids import (
    SchedulerDefinitionId,
    SchedulerExecutionId,
)
from shell.domain.scheduling.value_objects.interval_seconds import IntervalSeconds
from shell.domain.scheduling.value_objects.job_name import JobName
from shell.domain.scheduling.value_objects.job_type import JobType


class SchedulerJob(AggregateRoot[SchedulerExecutionId]):
    """Represents a cyclic job configuration run on an interval by APScheduler."""

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
        name: JobName,
        job_type: JobType,
        interval_seconds: IntervalSeconds,
        batch_size: BatchSize,
        enabled: Enabled = Enabled.yes(),
        config: StateData | None = None,
        created_at: CreatedAt | None = None,
        updated_at: Timestamp | None = None,
    ) -> None:
        super().__init__(id)
        self._scheduler_definition_id = scheduler_definition_id
        self._name = JobName(name) if isinstance(name, str) else name
        self._job_type = JobType(job_type) if isinstance(job_type, str) else job_type
        self._interval_seconds = (
            IntervalSeconds(interval_seconds) if isinstance(interval_seconds, (int, float)) else interval_seconds
        )
        self._batch_size = BatchSize(batch_size) if isinstance(batch_size, int) else batch_size
        self._enabled = enabled if isinstance(enabled, Enabled) else Enabled(enabled)
        self._config = StateData(config) if isinstance(config, dict) else (config or StateData({}))
        self._created_at = created_at or CreatedAt.now()
        self._updated_at = updated_at or Timestamp.now()

    @classmethod
    def restore(
        cls,
        id: SchedulerExecutionId,
        scheduler_definition_id: SchedulerDefinitionId,
        name: JobName,
        job_type: JobType,
        interval_seconds: IntervalSeconds,
        batch_size: BatchSize,
        enabled: Enabled = Enabled.yes(),
        config: StateData | None = None,
        created_at: CreatedAt | None = None,
        updated_at: Timestamp | None = None,
    ) -> Self:
        return cls(
            id=id,
            scheduler_definition_id=scheduler_definition_id,
            name=name,
            job_type=job_type,
            interval_seconds=interval_seconds,
            batch_size=batch_size,
            enabled=enabled,
            config=config,
            created_at=created_at,
            updated_at=updated_at,
        )

    @property
    def scheduler_definition_id(self) -> SchedulerDefinitionId:
        return self._scheduler_definition_id

    @property
    def name(self) -> JobName:
        return self._name

    @property
    def job_type(self) -> JobType:
        return self._job_type

    @property
    def interval_seconds(self) -> IntervalSeconds:
        return self._interval_seconds

    @property
    def batch_size(self) -> BatchSize:
        return self._batch_size

    @property
    def enabled(self) -> Enabled:
        return self._enabled

    @property
    def config(self) -> StateData:
        return self._config

    @property
    def created_at(self) -> CreatedAt:
        return self._created_at

    @property
    def updated_at(self) -> Timestamp:
        return self._updated_at
