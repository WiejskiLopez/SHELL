from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.error_description import ErrorDescription
from shell.platform.domain.value_objects.reason import Reason
from shell.platform.domain.value_objects.state_data import StateData
from shell.platform.domain.value_objects.updated_at import UpdatedAt
from shell.platform.types import JsonStr
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_execution.scheduler_execution import (
    SchedulerExecution,
)
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_execution.value_objects.execution_status import (
    ExecutionStatus,
)
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_execution.value_objects.scheduler_execution_id import (
    SchedulerExecutionId,
)
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_execution.value_objects.trigger_event_id import (
    TriggerEventId,
)
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_execution.value_objects.trigger_event_type import (
    TriggerEventType,
)

if TYPE_CHECKING:
    from shell.platform.domain.events import DomainEvent
    from shell.platform.domain.value_objects.timestamp import Timestamp
    from shell.scheduling_service.domain.scheduling.aggregates.scheduler_definition.scheduler_definition import (
        SchedulerDefinition,
    )


class SchedulerOrchestrator:
    def evaluate_definition(
        self,
        *,
        definition: SchedulerDefinition,
        trigger_event_id: str | None = None,
        trigger_event_type: str | None = None,
        input_state: dict[str, Any] | None = None,
        can_execute: bool,
        now: Timestamp,
    ) -> SchedulerExecution:
        execution = SchedulerExecution(
            id=SchedulerExecutionId.generate(),
            scheduler_definition_id=definition.id,
            status=ExecutionStatus.PENDING,
            trigger_event_id=TriggerEventId(trigger_event_id) if trigger_event_id else None,
            trigger_event_type=TriggerEventType(trigger_event_type) if trigger_event_type else None,
            input_state=StateData(JsonStr(json.dumps(input_state))) if input_state else None,
            created_at=CreatedAt.from_datetime(now.value),
            updated_at=UpdatedAt.from_datetime(now.value),
        )

        if not can_execute:
            execution.skip(reason=Reason("execution_checker rejected"), now=now)
            return execution

        if definition.action_config.action_type != "spawn_graph":
            execution.skip(
                reason=Reason(f"unsupported action_type: {definition.action_config.action_type}"),
                now=now,
            )
            return execution

        if definition.action_config.graph_definition_id is None:
            execution.skip(reason=Reason("no graph_definition_id in action_config"), now=now)
            return execution

        return execution

    def start_execution(
        self,
        execution: SchedulerExecution,
        *,
        action_ref: str,
        action_ref_type: str,
        now: Timestamp,
    ) -> list[DomainEvent]:
        execution.start(
            action_ref=action_ref,
            action_ref_type=action_ref_type,
            now=now,
        )
        return execution.pull_events()

    def complete_execution(
        self,
        execution: SchedulerExecution,
        *,
        output_state: dict[str, Any] | None = None,
        error: str | None = None,
        now: Timestamp,
    ) -> list[DomainEvent]:
        if error:
            execution.fail(error=ErrorDescription(error), now=now)
        else:
            execution.complete(
                output_state=StateData(JsonStr(json.dumps(output_state))) if output_state else None,
                now=now,
            )
        return execution.pull_events()
