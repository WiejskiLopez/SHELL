from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.scheduling.domain.scheduling.aggregates.scheduler_execution.scheduler_execution import (
        SchedulerExecution,
    )
    from shell.scheduling.infrastructure.scheduling.scheduler_job.persistence.sql.models.scheduler_job import (
        SchedulerJobModel,
    )


def scheduler_job_update_model(model: SchedulerJobModel, entity: SchedulerExecution) -> None:
    model.status = entity.status.value
    model.trigger_event_id = entity.trigger_event_id.value if entity.trigger_event_id else None
    model.trigger_event_type = (
        entity.trigger_event_type.value if entity.trigger_event_type else None
    )
    model.action_ref = entity.action_ref.value if entity.action_ref else None
    model.action_ref_type = entity.action_ref_type.value if entity.action_ref_type else None
    model.error = entity.error.value if entity.error else None
    model.started_at = entity.started_at.value if entity.started_at else None
    model.completed_at = entity.completed_at.value if entity.completed_at else None
    model.updated_at = entity.updated_at.value
