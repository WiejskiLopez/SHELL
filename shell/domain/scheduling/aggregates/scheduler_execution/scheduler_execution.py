from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

from shell.domain.scheduling.aggregates.scheduler_execution.events import (
    SchedulerExecutionCompletedEvent,
    SchedulerExecutionFailedEvent,
    SchedulerExecutionSkippedEvent,
    SchedulerExecutionStartedEvent,
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
from shell.platform.domain.base import AggregateRoot
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.error_description import ErrorDescription
from shell.platform.domain.value_objects.reason import Reason
from shell.platform.domain.value_objects.state_data import StateData
from shell.platform.domain.value_objects.timestamp import Timestamp

if TYPE_CHECKING:
    from shell.domain.scheduling.aggregates.scheduler_definition.value_objects.scheduler_definition_id import (
        SchedulerDefinitionId,
    )


class SchedulerExecution(AggregateRoot[SchedulerExecutionId]):
    """Represents a one-shot evaluation of a SchedulerDefinition."""

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
        created_at: CreatedAt,
        updated_at: Timestamp,
        status: ExecutionStatus,
        trigger_event_id: TriggerEventId | None = None,
        trigger_event_type: TriggerEventType | None = None,
        action_ref: ActionRef | None = None,
        action_ref_type: ActionRefType | None = None,
        input_state: StateData | None = None,
        output_state: StateData | None = None,
        error: ErrorDescription | None = None,
        started_at: Timestamp | None = None,
        completed_at: Timestamp | None = None,
    ) -> None:
        super().__init__(id)
        self._scheduler_definition_id = scheduler_definition_id
        self._status = ExecutionStatus(status) if isinstance(status, str) else status
        self._trigger_event_id = (
            TriggerEventId(trigger_event_id)
            if isinstance(trigger_event_id, str)
            else trigger_event_id
        )
        self._trigger_event_type = (
            TriggerEventType(trigger_event_type)
            if isinstance(trigger_event_type, str)
            else trigger_event_type
        )
        self._action_ref = ActionRef(action_ref) if isinstance(action_ref, str) else action_ref
        self._action_ref_type = (
            ActionRefType(action_ref_type) if isinstance(action_ref_type, str) else action_ref_type
        )
        self._input_state = input_state
        self._output_state = output_state
        self._error = error
        self._started_at = started_at
        self._completed_at = completed_at
        self._created_at = created_at
        self._updated_at = updated_at

    @classmethod
    def restore(
        cls,
        id: SchedulerExecutionId,
        scheduler_definition_id: SchedulerDefinitionId,
        created_at: CreatedAt,
        updated_at: Timestamp,
        status: ExecutionStatus,
        trigger_event_id: TriggerEventId | None = None,
        trigger_event_type: TriggerEventType | None = None,
        action_ref: ActionRef | None = None,
        action_ref_type: ActionRefType | None = None,
        input_state: StateData | None = None,
        output_state: StateData | None = None,
        error: ErrorDescription | None = None,
        started_at: Timestamp | None = None,
        completed_at: Timestamp | None = None,
    ) -> Self:
        return cls(
            id=id,
            scheduler_definition_id=scheduler_definition_id,
            status=status,
            trigger_event_id=trigger_event_id,
            trigger_event_type=trigger_event_type,
            action_ref=action_ref,
            action_ref_type=action_ref_type,
            input_state=input_state,
            output_state=output_state,
            error=error,
            started_at=started_at,
            completed_at=completed_at,
            created_at=created_at,
            updated_at=updated_at,
        )

    @property
    def scheduler_definition_id(self) -> SchedulerDefinitionId:
        return self._scheduler_definition_id

    @property
    def status(self) -> ExecutionStatus:
        return self._status

    @property
    def trigger_event_id(self) -> TriggerEventId | None:
        return self._trigger_event_id

    @property
    def trigger_event_type(self) -> TriggerEventType | None:
        return self._trigger_event_type

    @property
    def action_ref(self) -> ActionRef | None:
        return self._action_ref

    @property
    def action_ref_type(self) -> ActionRefType | None:
        return self._action_ref_type

    @property
    def input_state(self) -> StateData | None:
        return self._input_state

    @property
    def output_state(self) -> StateData | None:
        return self._output_state

    @property
    def error(self) -> ErrorDescription | None:
        return self._error

    @property
    def started_at(self) -> Timestamp | None:
        return self._started_at

    @property
    def completed_at(self) -> Timestamp | None:
        return self._completed_at

    @property
    def created_at(self) -> CreatedAt:
        return self._created_at

    @property
    def updated_at(self) -> Timestamp:
        return self._updated_at

    def start(
        self, action_ref: ActionRef | str, action_ref_type: ActionRefType | str, now: Timestamp
    ) -> None:
        self._status = ExecutionStatus.EXECUTING
        self._action_ref = ActionRef(action_ref) if isinstance(action_ref, str) else action_ref
        self._action_ref_type = (
            ActionRefType(action_ref_type) if isinstance(action_ref_type, str) else action_ref_type
        )
        self._started_at = now
        self._updated_at = now
        self.append_event(
            SchedulerExecutionStartedEvent(
                occurred_at=CreatedAt.from_datetime(now.value),
                execution_id=self.id,
                action_ref=self._action_ref,
                action_ref_type=self._action_ref_type,
            )
        )

    def complete(
        self, output_state: StateData | dict[str, Any] | None = None, now: Timestamp | None = None
    ) -> None:
        if now is None:
            now = Timestamp.now()
        self._status = ExecutionStatus.COMPLETED
        actual_state = StateData(output_state) if isinstance(output_state, dict) else output_state
        self._output_state = actual_state
        self._completed_at = now
        self._updated_at = now
        self.append_event(
            SchedulerExecutionCompletedEvent(
                occurred_at=CreatedAt.from_datetime(now.value),
                execution_id=self.id,
                output_state=self._output_state,
            )
        )

    def fail(
        self, error: ErrorDescription | str | None = None, now: Timestamp | None = None
    ) -> None:
        if now is None:
            now = Timestamp.now()
        self._status = ExecutionStatus.FAILED
        self._error = ErrorDescription(error) if isinstance(error, str) else error
        self._completed_at = now
        self._updated_at = now
        self.append_event(
            SchedulerExecutionFailedEvent(
                occurred_at=CreatedAt.from_datetime(now.value),
                execution_id=self.id,
                error=self._error,
            )
        )

    def skip(self, reason: Reason | str, now: Timestamp | None = None) -> None:
        if now is None:
            now = Timestamp.now()
        self._status = ExecutionStatus.SKIPPED
        self._completed_at = now
        self._updated_at = now
        actual_reason = Reason(reason) if isinstance(reason, str) else reason
        self.append_event(
            SchedulerExecutionSkippedEvent(
                occurred_at=CreatedAt.from_datetime(now.value),
                execution_id=self.id,
                reason=actual_reason,
            )
        )
