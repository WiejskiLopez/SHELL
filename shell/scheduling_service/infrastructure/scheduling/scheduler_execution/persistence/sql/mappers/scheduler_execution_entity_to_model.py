from __future__ import annotations

import json
from typing import TYPE_CHECKING, cast

from shell.scheduling_service.infrastructure.scheduling.scheduler_execution.persistence.sql.models.scheduler_execution import (
    SchedulerExecutionModel,
)

if TYPE_CHECKING:
    from shell.scheduling_service.domain.scheduling.aggregates.scheduler_execution.scheduler_execution import (
        SchedulerExecution,
    )


def scheduler_execution_entity_to_model(entity: SchedulerExecution) -> SchedulerExecutionModel:
    def _state_to_dict(state: object | None) -> dict[str, object] | None:
        if state is None:
            return None
        raw: str = (
            state.value.value
            if hasattr(state, "value") and hasattr(state.value, "value")
            else str(state)
        )
        try:
            return cast("dict[str, object] | None", json.loads(raw))
        except (json.JSONDecodeError, TypeError):
            return None

    return SchedulerExecutionModel(
        id=entity.id.value,
        scheduler_definition_id=entity.scheduler_definition_id.value,
        status=entity.status.value,
        trigger_event_id=entity.trigger_event_id.value if entity.trigger_event_id else None,
        trigger_event_type=entity.trigger_event_type.value if entity.trigger_event_type else None,
        action_ref=entity.action_ref.value if entity.action_ref else None,
        action_ref_type=entity.action_ref_type.value if entity.action_ref_type else None,
        input_state=_state_to_dict(entity.input_state),
        output_state=_state_to_dict(entity.output_state),
        error=entity.error.value if entity.error else None,
        started_at=entity.started_at.value if entity.started_at else None,
        completed_at=entity.completed_at.value if entity.completed_at else None,
        created_at=entity.created_at.value,
        updated_at=entity.updated_at.value,
    )
