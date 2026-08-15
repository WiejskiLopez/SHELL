from __future__ import annotations

import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.scheduling_service.domain.scheduling.aggregates.scheduler_execution.scheduler_execution import (
        SchedulerExecution,
    )
    from shell.scheduling_service.infrastructure.scheduling.scheduler_execution.persistence.sql.models.scheduler_execution import (
        SchedulerExecutionModel,
    )


def scheduler_execution_change_model(
    model: SchedulerExecutionModel, entity: SchedulerExecution
) -> None:
    model.scheduler_definition_id = entity.scheduler_definition_id.value
    model.status = entity.status.value
    model.trigger_event_id = entity.trigger_event_id.value if entity.trigger_event_id else None
    model.trigger_event_type = (
        entity.trigger_event_type.value if entity.trigger_event_type else None
    )
    model.action_ref = entity.action_ref.value if entity.action_ref else None
    model.action_ref_type = entity.action_ref_type.value if entity.action_ref_type else None
    if entity.input_state is not None:
        model.input_state = json.loads(entity.input_state.value.value)
    if entity.output_state is not None:
        model.output_state = json.loads(entity.output_state.value.value)
    model.error = entity.error.value if entity.error else None
    model.started_at = entity.started_at.value if entity.started_at else None
    model.completed_at = entity.completed_at.value if entity.completed_at else None
    model.changed_at = entity.changed_at.value
