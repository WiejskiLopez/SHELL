from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shell.platform.domain.value_objects.changed_at import ChangedAt
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.enabled import Enabled
from shell.platform.domain.value_objects.state_data import StateData
from shell.platform.types import JsonStr
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_definition.value_objects.scheduler_definition_id import (
    SchedulerDefinitionId,
)
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_job.scheduler_job import (
    SchedulerJob,
)
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_job.value_objects.batch_size import (
    BatchSize,
)
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_job.value_objects.interval_seconds import (
    IntervalSeconds,
)
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_job.value_objects.job_name import (
    JobName,
)
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_job.value_objects.job_type import (
    JobType,
)
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_job.value_objects.scheduler_job_id import (
    SchedulerJobId,
)

if TYPE_CHECKING:
    from shell.scheduling_service.infrastructure.scheduling.scheduler_job.persistence.sql.models.scheduler_job import (
        SchedulerJobModel,
    )


def scheduler_job_model_to_entity(model: SchedulerJobModel) -> SchedulerJob:
    return SchedulerJob.restore(
        id=SchedulerJobId(model.id),
        scheduler_definition_id=SchedulerDefinitionId(model.scheduler_definition_id),
        name=JobName(model.name),
        job_type=JobType(model.job_type),
        interval_seconds=IntervalSeconds(model.interval_seconds),
        batch_size=BatchSize(model.batch_size),
        enabled=Enabled(model.enabled),
        config=StateData(JsonStr(json.dumps(dict(model.config))))
        if model.config
        else StateData(JsonStr("{}")),
        created_at=CreatedAt.from_datetime(model.created_at),
        changed_at=ChangedAt.from_datetime(model.changed_at),
    )
