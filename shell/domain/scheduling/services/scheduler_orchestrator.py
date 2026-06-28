from __future__ import annotations

from typing import TYPE_CHECKING, Any

from shell.domain.scheduling.aggregates.scheduler_execution.scheduler_execution import (
    SchedulerExecution,
)
from shell.domain.scheduling.aggregates.scheduler_execution.value_objects.execution_status import (
    ExecutionStatus,
)
from shell.domain.scheduling.value_objects.ids import (
    SchedulerExecutionId,
)

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.platform.events import DomainEvent
    from shell.domain.scheduling.aggregates.scheduler_definition.scheduler_definition import (
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
        now: datetime,
    ) -> SchedulerExecution:
        execution = SchedulerExecution(
            id=SchedulerExecutionId.generate(),
            scheduler_definition_id=definition.id,
            status=ExecutionStatus.PENDING,
            trigger_event_id=trigger_event_id,
            trigger_event_type=trigger_event_type,
            input_state=input_state,
            created_at=now,
            updated_at=now,
        )

        if not can_execute:
            execution.skip(reason="execution_checker rejected", now=now)
            return execution

        if definition.action_config.action_type != "spawn_graph":
            execution.skip(
                reason=f"unsupported action_type: {definition.action_config.action_type}",
                now=now,
            )
            return execution

        if definition.action_config.graph_definition_id is None:
            execution.skip(reason="no graph_definition_id in action_config", now=now)
            return execution

        return execution

    def start_execution(
        self,
        execution: SchedulerExecution,
        *,
        action_ref: str,
        action_ref_type: str,
        now: datetime,
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
        now: datetime,
    ) -> list[DomainEvent]:
        if error:
            execution.fail(error=error, now=now)
        else:
            execution.complete(output_state=output_state, now=now)
        return execution.pull_events()
