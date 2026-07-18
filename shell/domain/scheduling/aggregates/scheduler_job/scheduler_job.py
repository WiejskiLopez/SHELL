from __future__ import annotations

from typing import TYPE_CHECKING, Self

from scheduling.aggregates.scheduler_job.events.schedulerjob_deleted_event import (
    SchedulerJobDeletedEvent,
)
from scheduling.aggregates.scheduler_job.events.schedulerjob_updated_event import (
    SchedulerJobUpdatedEvent,
)

from shell.domain.scheduling.aggregates.scheduler_execution.value_objects.scheduler_execution_id import (
    SchedulerExecutionId,
)
from shell.domain.scheduling.aggregates.scheduler_job.events.scheduler_job_created_event import (
    SchedulerJobCreatedEvent,
)
from shell.domain.scheduling.aggregates.scheduler_job.value_objects.batch_size import BatchSize
from shell.domain.scheduling.aggregates.scheduler_job.value_objects.interval_seconds import (
    IntervalSeconds,
)
from shell.domain.scheduling.aggregates.scheduler_job.value_objects.job_name import JobName
from shell.domain.scheduling.aggregates.scheduler_job.value_objects.job_type import JobType
from shell.platform.domain.base import AggregateRoot
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.enabled import Enabled
from shell.platform.domain.value_objects.updated_at import UpdatedAt

if TYPE_CHECKING:
    from shell.domain.scheduling.aggregates.scheduler_definition.value_objects.scheduler_definition_id import (
        SchedulerDefinitionId,
    )
    from shell.platform.domain.value_objects.deleted_at import DeletedAt
    from shell.platform.domain.value_objects.state_data import StateData
    from shell.platform.domain.value_objects.timestamp import Timestamp

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
        enabled: Enabled,
        config: StateData,
        created_at: CreatedAt,
        updated_at: Timestamp,
    ) -> None:
        super().__init__(id)
        self._scheduler_definition_id = scheduler_definition_id
        self._name = JobName(name) if isinstance(name, str) else name
        self._job_type = JobType(job_type) if isinstance(job_type, str) else job_type
        self._interval_seconds = (
            IntervalSeconds(interval_seconds)
            if isinstance(interval_seconds, (int, float))
            else interval_seconds
        )
        self._batch_size = BatchSize(batch_size) if isinstance(batch_size, int) else batch_size
        self._enabled = enabled if isinstance(enabled, Enabled) else Enabled(enabled)
        self._config = config
        self._created_at = created_at
        self._updated_at = updated_at

    @classmethod
    def create(
        cls,
        *,
        id_: SchedulerExecutionId,
        scheduler_definition_id: SchedulerDefinitionId,
        name: JobName,
        job_type: JobType,
        interval_seconds: IntervalSeconds,
        batch_size: BatchSize,
        config: StateData,
        now: CreatedAt,
        enabled: bool = True,
    ) -> SchedulerJob:
        return cls._new(id_=id_, scheduler_definition_id=scheduler_definition_id, name=name, job_type=job_type, interval_seconds=interval_seconds, batch_size=batch_size, config=config, now=now, enabled=enabled)

    @classmethod
    def restore(
        cls,
        id: SchedulerExecutionId,
        scheduler_definition_id: SchedulerDefinitionId,
        name: JobName,
        job_type: JobType,
        interval_seconds: IntervalSeconds,
        batch_size: BatchSize,
        enabled: Enabled,
        config: StateData,
        created_at: CreatedAt,
        updated_at: Timestamp,
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

    @classmethod
    def _new(
        cls,
        *,
        id_: SchedulerExecutionId,
        scheduler_definition_id: SchedulerDefinitionId,
        name: JobName,
        job_type: JobType,
        interval_seconds: IntervalSeconds,
        batch_size: BatchSize,
        config: StateData,
        now: CreatedAt,
        enabled: bool = True,
    ) -> SchedulerJob:
        instance = cls(
            id=id_,
            scheduler_definition_id=scheduler_definition_id,
            name=name,
            job_type=job_type,
            interval_seconds=interval_seconds,
            batch_size=batch_size,
            enabled=Enabled(enabled),
            config=config,
            created_at=now,
        )

        instance.append_event(
            SchedulerJobCreatedEvent.now(
                schedulerjob_id=instance.id,
                now=now,
            )
        )
        return instance

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._updated_at = UpdatedAt.from_datetime(now.value)
        self.append_event(
            SchedulerJobDeletedEvent.now(
                schedulerjob_id=self._id,
                now=CreatedAt.from_datetime(now.value),
            )
        )
    def _update(self, now: UpdatedAt) -> None:
        self._updated_at = now
        self.append_event(
            SchedulerJobUpdatedEvent.now(
                schedulerjob_id=self._id,
                now=CreatedAt.from_datetime(now.value),
            )
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
