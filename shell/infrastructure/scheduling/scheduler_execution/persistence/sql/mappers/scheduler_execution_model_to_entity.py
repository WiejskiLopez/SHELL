import json
from datetime import UTC, datetime

from shell.domain.scheduling.aggregates.scheduler_definition.value_objects.scheduler_definition_id import (
    SchedulerDefinitionId,
)
from shell.domain.scheduling.aggregates.scheduler_execution.value_objects.scheduler_execution_id import (
    SchedulerExecutionId,
)
from shell.domain.scheduling.aggregates.scheduler_job.scheduler_job import (
    SchedulerJob,
)
from shell.domain.scheduling.aggregates.scheduler_job.value_objects.batch_size import BatchSize
from shell.domain.scheduling.aggregates.scheduler_job.value_objects.interval_seconds import (
    IntervalSeconds,
)
from shell.domain.scheduling.aggregates.scheduler_job.value_objects.job_name import JobName
from shell.domain.scheduling.aggregates.scheduler_job.value_objects.job_type import JobType
from shell.infrastructure.scheduling.scheduler_execution.persistence.sql.models.scheduler_execution import (
    SchedulerExecutionModel,
)
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.enabled import Enabled
from shell.platform.domain.value_objects.state_data import StateData
from shell.platform.domain.value_objects.timestamp import Timestamp
from shell.platform.types import JsonStr  # noqa: TC001


def scheduler_execution_model_to_entity(
    model: SchedulerExecutionModel,
) -> SchedulerJob:
    return SchedulerJob.restore(
        id=SchedulerExecutionId(model.id),
        scheduler_definition_id=SchedulerDefinitionId(model.scheduler_definition_id),
        name=JobName(model.name),
        job_type=JobType(model.job_type),
        interval_seconds=IntervalSeconds(model.interval_seconds),
        batch_size=BatchSize(model.batch_size),
        enabled=Enabled(model.enabled),
        config=StateData(JsonStr(json.dumps(dict(model.config)))) if model.config else StateData(JsonStr("{}")),
        created_at=CreatedAt.from_datetime(model.created_at),
        updated_at=Timestamp.from_datetime(model.updated_at),
    )

