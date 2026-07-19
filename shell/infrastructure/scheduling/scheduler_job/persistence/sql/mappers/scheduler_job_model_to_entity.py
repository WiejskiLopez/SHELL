from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shell.domain.scheduling.aggregates.scheduler_definition.value_objects.scheduler_definition_id import (
    SchedulerDefinitionId,
)
from shell.domain.scheduling.aggregates.scheduler_execution.scheduler_execution import (
    SchedulerExecution,
)
from shell.domain.scheduling.aggregates.scheduler_execution.value_objects.action_ref import (
    ActionRef,
)
from shell.domain.scheduling.aggregates.scheduler_execution.value_objects.action_ref_type import (
    ActionRefType,
)
from shell.domain.scheduling.aggregates.scheduler_execution.value_objects.execution_status import (
    ExecutionStatus,
)
from shell.domain.scheduling.aggregates.scheduler_execution.value_objects.scheduler_execution_id import (
    SchedulerExecutionId,
)
from shell.domain.scheduling.aggregates.scheduler_execution.value_objects.trigger_event_id import (
    TriggerEventId,
)
from shell.domain.scheduling.aggregates.scheduler_execution.value_objects.trigger_event_type import (
    TriggerEventType,
)
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.error_description import ErrorDescription
from shell.platform.domain.value_objects.state_data import StateData
from shell.platform.domain.value_objects.timestamp import Timestamp
from shell.platform.domain.value_objects.updated_at import UpdatedAt
from shell.platform.types import JsonStr

if TYPE_CHECKING:
    from shell.infrastructure.scheduling.scheduler_job.persistence.sql.models.scheduler_job import (
        SchedulerJobModel,
    )


def scheduler_job_model_to_entity(model: SchedulerJobModel) -> SchedulerExecution:
    def _dict_to_state(d: object | None) -> StateData | None:
        if d is None:
            return None
        if isinstance(d, dict):
            return StateData(JsonStr(json.dumps(d)))
        return StateData(JsonStr(str(d)))

    return SchedulerExecution.restore(
        id=SchedulerExecutionId(model.id),
        scheduler_definition_id=SchedulerDefinitionId(model.scheduler_definition_id),
        status=ExecutionStatus(model.status),
        trigger_event_id=TriggerEventId(model.trigger_event_id) if model.trigger_event_id else None,
        trigger_event_type=TriggerEventType(model.trigger_event_type)
        if model.trigger_event_type
        else None,
        action_ref=ActionRef(model.action_ref) if model.action_ref else None,
        action_ref_type=ActionRefType(model.action_ref_type) if model.action_ref_type else None,
        input_state=_dict_to_state(model.input_state),
        output_state=_dict_to_state(model.output_state),
        error=ErrorDescription(model.error) if model.error else None,
        started_at=Timestamp.from_datetime(model.started_at) if model.started_at else None,
        completed_at=Timestamp.from_datetime(model.completed_at) if model.completed_at else None,
        created_at=CreatedAt.from_datetime(model.created_at),
        updated_at=UpdatedAt.from_datetime(model.updated_at),
    )
