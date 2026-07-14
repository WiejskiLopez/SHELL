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


def scheduler_execution_entity_to_model(
    entity: SchedulerJob,
) -> SchedulerExecutionModel:
    return SchedulerExecutionModel(
        id=entity.id.value,
        scheduler_definition_id=entity.scheduler_definition_id.value,
        name=entity.name.value,
        job_type=entity.job_type.value,
        interval_seconds=entity.interval_seconds.value,
        batch_size=entity.batch_size.value,
        enabled=entity.enabled.value,
        config=json.dumps(json.loads(entity.config.value.value)),
        created_at=entity.created_at.value,
        updated_at=entity.updated_at.value,
    )

