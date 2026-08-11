from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shell.scheduling.infrastructure.scheduling.scheduler_execution.persistence.sql.models.scheduler_execution import (
    SchedulerExecutionModel,
)

if TYPE_CHECKING:
    from shell.scheduling.domain.scheduling.aggregates.scheduler_job.scheduler_job import (
        SchedulerJob,
    )


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
