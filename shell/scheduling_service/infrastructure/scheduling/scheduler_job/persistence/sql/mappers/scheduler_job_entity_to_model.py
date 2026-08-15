from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shell.scheduling_service.infrastructure.scheduling.scheduler_job.persistence.sql.models.scheduler_job import (
    SchedulerJobModel,
)

if TYPE_CHECKING:
    from shell.scheduling_service.domain.scheduling.aggregates.scheduler_job.scheduler_job import (
        SchedulerJob,
    )


def scheduler_job_entity_to_model(entity: SchedulerJob) -> SchedulerJobModel:
    return SchedulerJobModel(
        id=entity.id.value,
        scheduler_definition_id=entity.scheduler_definition_id.value,
        name=entity.name.value,
        job_type=entity.job_type.value,
        interval_seconds=entity.interval_seconds.value,
        batch_size=entity.batch_size.value,
        enabled=entity.enabled.value,
        config=json.loads(entity.config.value.value),
        created_at=entity.created_at.value,
        updated_at=entity.updated_at.value,
    )
