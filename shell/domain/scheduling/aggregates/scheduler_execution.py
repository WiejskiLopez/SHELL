from __future__ import annotations

from datetime import datetime
from typing import Any

from shell.domain.platform.base import AggregateRoot
from shell.domain.scheduling.events.scheduler_execution_completed_event import (
    SchedulerExecutionCompletedEvent,
)
from shell.domain.scheduling.events.scheduler_execution_failed_event import (
    SchedulerExecutionFailedEvent,
)
from shell.domain.scheduling.events.scheduler_execution_skipped_event import (
    SchedulerExecutionSkippedEvent,
)
from shell.domain.scheduling.events.scheduler_execution_started_event import (
    SchedulerExecutionStartedEvent,
)
from shell.domain.scheduling.value_objects.execution_status import ExecutionStatus
from shell.domain.scheduling.value_objects.ids import (
    SchedulerDefinitionId,
    SchedulerExecutionId,
)


class SchedulerExecution(AggregateRoot[SchedulerExecutionId]):
    __slots__ = (
        "_scheduler_definition_id",
        "_status",
        "_trigger_event_id",
        "_trigger_event_type",
        "_action_ref",
        "_action_ref_type",
        "_input_state",
        "_output_state",
        "_error",
        "_started_at",
        "_completed_at",
        "_created_at",
        "_updated_at",
    )

    def __init__(
        self,
        id: SchedulerExecutionId,
        scheduler_definition_id: SchedulerDefinitionId,
        status: ExecutionStatus | str = ExecutionStatus.PENDING,
        trigger_event_id: str | None = None,
        trigger_event_type: str | None = None,
        action_ref: str | None = None,
        action_ref_type: str | None = None,
        input_state: dict[str, Any] | None = None,
        output_state: dict[str, Any] | None = None,
        error: str | None = None,
        started_at: datetime | None = None,
        completed_at: datetime | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        super().__init__(id)
        self._scheduler_definition_id = scheduler_definition_id
        self._status = ExecutionStatus(status) if isinstance(status, str) else status
        self._trigger_event_id = trigger_event_id
        self._trigger_event_type = trigger_event_type
        self._action_ref = action_ref
        self._action_ref_type = action_ref_type
        self._input_state = input_state or {}
        self._output_state = output_state or {}
        self._error = error
        self._started_at = started_at
        self._completed_at = completed_at
        self._created_at = created_at or datetime.now()
        self._updated_at = updated_at or datetime.now()

    @property
    def scheduler_definition_id(self) -> SchedulerDefinitionId:
        return self._scheduler_definition_id

    @property
    def status(self) -> ExecutionStatus:
        return self._status

    @property
    def trigger_event_id(self) -> str | None:
        return self._trigger_event_id

    @property
    def trigger_event_type(self) -> str | None:
        return self._trigger_event_type

    @property
    def action_ref(self) -> str | None:
        return self._action_ref

    @property
    def action_ref_type(self) -> str | None:
        return self._action_ref_type

    @property
    def input_state(self) -> dict[str, Any]:
        return dict(self._input_state)

    @property
    def output_state(self) -> dict[str, Any]:
        return dict(self._output_state)

    @property
    def error(self) -> str | None:
        return self._error

    @property
    def started_at(self) -> datetime | None:
        return self._started_at

    @property
    def completed_at(self) -> datetime | None:
        return self._completed_at

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    def start(self, action_ref: str, action_ref_type: str, now: datetime) -> None:
        self._status = ExecutionStatus.EXECUTING
        self._action_ref = action_ref
        self._action_ref_type = action_ref_type
        self._started_at = now
        self._updated_at = now
        self.append_event(
            SchedulerExecutionStartedEvent.now(
                scheduler_execution_id=self.id,
                scheduler_definition_id=self._scheduler_definition_id,
                action_ref=action_ref,
                action_ref_type=action_ref_type,
                now=now,
            )
        )

    def complete(
        self, output_state: dict[str, Any] | None = None, now: datetime | None = None
    ) -> None:
        if now is None:
            now = datetime.now()
        self._status = ExecutionStatus.COMPLETED
        self._output_state = dict(output_state) if output_state else {}
        self._completed_at = now
        self._updated_at = now
        self.append_event(
            SchedulerExecutionCompletedEvent.now(
                scheduler_execution_id=self.id,
                scheduler_definition_id=self._scheduler_definition_id,
                output_state=self._output_state,
                action_ref=self._action_ref,
                now=now,
            )
        )

    def fail(self, error: str, now: datetime | None = None) -> None:
        if now is None:
            now = datetime.now()
        self._status = ExecutionStatus.FAILED
        self._error = error
        self._completed_at = now
        self._updated_at = now
        self.append_event(
            SchedulerExecutionFailedEvent.now(
                scheduler_execution_id=self.id,
                scheduler_definition_id=self._scheduler_definition_id,
                error=error,
                action_ref=self._action_ref,
                now=now,
            )
        )

    def skip(self, reason: str, now: datetime | None = None) -> None:
        if now is None:
            now = datetime.now()
        self._status = ExecutionStatus.SKIPPED
        self._completed_at = now
        self._updated_at = now
        self.append_event(
            SchedulerExecutionSkippedEvent.now(
                scheduler_execution_id=self.id,
                scheduler_definition_id=self._scheduler_definition_id,
                reason=reason,
                now=now,
            )
        )
