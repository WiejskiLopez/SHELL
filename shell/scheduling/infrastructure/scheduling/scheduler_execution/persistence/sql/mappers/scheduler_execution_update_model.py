from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.scheduling.domain.scheduling.aggregates.scheduler_job.scheduler_job import (
        SchedulerJob,
    )
    from shell.scheduling.infrastructure.scheduling.scheduler_execution.persistence.sql.models.scheduler_execution import (
        SchedulerExecutionModel,
    )


def scheduler_execution_update_model(model: SchedulerExecutionModel, entity: SchedulerJob) -> None:
    model.scheduler_definition_id = entity.scheduler_definition_id.value
    model.name = entity.name.value
    model.job_type = entity.job_type.value
    model.interval_seconds = entity.interval_seconds.value
    model.batch_size = entity.batch_size.value
    model.enabled = entity.enabled.value
    model.config = json.dumps(json.loads(entity.config.value.value))  # type: ignore[assignment]
    model.updated_at = entity.updated_at.value  # type: ignore[assignment]
