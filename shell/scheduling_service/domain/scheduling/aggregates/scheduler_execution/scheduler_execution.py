from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.platform.domain.base import AggregateRoot
from shell.platform.domain.exceptions.domain_error import DomainError
from shell.platform.domain.value_objects.changed_at import NONE_CHANGED_AT, ChangedAt
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.error_description import ErrorDescription
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.domain.value_objects.timestamp import Timestamp
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_execution.events import (
    SchedulerExecutionCompletedEvent,
    SchedulerExecutionFailedEvent,
    SchedulerExecutionSkippedEvent,
    SchedulerExecutionStartedEvent,
)
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_execution.events.scheduler_execution_changed_event import (
    SchedulerExecutionChangedEvent,
)
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_execution.events.scheduler_execution_created_event import (
    SchedulerExecutionCreatedEvent,
)
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_execution.events.scheduler_execution_deleted_event import (
    SchedulerExecutionDeletedEvent,
)
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_execution.value_objects.action_ref import (
    ActionRef,
)
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_execution.value_objects.action_ref_type import (
    ActionRefType,
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
    from shell.platform.domain.value_objects.deleted_at import DeletedAt
    from shell.platform.domain.value_objects.reason import Reason
    from shell.platform.domain.value_objects.state_data import StateData
    from shell.scheduling_service.domain.scheduling.aggregates.scheduler_definition.value_objects.scheduler_definition_id import (
        SchedulerDefinitionId,
    )


class SchedulerExecution(AggregateRoot[SchedulerExecutionId]):
    """Represents a one-shot evaluation of a SchedulerDefinition."""

    __slots__ = (
        "_created_at",
        "_changed_at",
        "_deleted_at",
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
    )

    def __init__(
        self,
        *,
        id: SchedulerExecutionId,
        created_at: CreatedAt,
        changed_at: ChangedAt = NONE_CHANGED_AT,
        scheduler_definition_id: SchedulerDefinitionId,
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
        self._changed_at = changed_at

    @classmethod
    def create(
        cls,
        *,
        id_: SchedulerExecutionId,
        now: CreatedAt,
        scheduler_definition_id: SchedulerDefinitionId,
    ) -> SchedulerExecution:
        return cls._new(
            id_=id_,
            scheduler_definition_id=scheduler_definition_id,
            now=OccurredAt.from_datetime(now.value),
        )

    @classmethod
    def restore(
        cls,
        *,
        id: SchedulerExecutionId,
        created_at: CreatedAt,
        changed_at: ChangedAt = NONE_CHANGED_AT,
        scheduler_definition_id: SchedulerDefinitionId,
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
            changed_at=changed_at,
        )

    @classmethod
    def _new(
        cls,
        *,
        id_: SchedulerExecutionId,
        now: OccurredAt,
        scheduler_definition_id: SchedulerDefinitionId,
    ) -> SchedulerExecution:
        instance = cls(
            id=id_,
            scheduler_definition_id=scheduler_definition_id,
            status=ExecutionStatus.PENDING,
            created_at=CreatedAt.from_datetime(now.value),
        )
        instance.append_event(
            SchedulerExecutionCreatedEvent.now(
                scheduler_execution_id=id_,
                now=OccurredAt.from_datetime(now.value),
            )
        )
        return instance

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            SchedulerExecutionDeletedEvent.now(
                scheduler_execution_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def _change(self, now: OccurredAt) -> None:
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            SchedulerExecutionChangedEvent.now(
                scheduler_execution_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
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
    def changed_at(self) -> ChangedAt:
        return self._changed_at

    def start(
        self, action_ref: ActionRef | str, action_ref_type: ActionRefType | str, now: Timestamp
    ) -> None:
        if self._status != ExecutionStatus.PENDING:
            raise DomainError(f"Cannot start execution in status {self._status!r}")
        self._status = ExecutionStatus.EXECUTING
        self._action_ref = ActionRef(action_ref) if isinstance(action_ref, str) else action_ref
        self._action_ref_type = (
            ActionRefType(action_ref_type) if isinstance(action_ref_type, str) else action_ref_type
        )
        self._started_at = now
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            SchedulerExecutionStartedEvent(
                occurred_at=OccurredAt.from_datetime(now.value),
                execution_id=self.id,
            )
        )

    def complete(self, output_state: StateData | None = None, now: Timestamp | None = None) -> None:
        if self._status != ExecutionStatus.EXECUTING:
            raise DomainError(f"Cannot complete execution in status {self._status!r}")
        if now is None:
            now = Timestamp.now()
        self._status = ExecutionStatus.COMPLETED
        self._output_state = output_state
        self._completed_at = now
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            SchedulerExecutionCompletedEvent(
                occurred_at=OccurredAt.from_datetime(now.value),
                execution_id=self.id,
            )
        )

    def fail(
        self, error: ErrorDescription | str | None = None, now: Timestamp | None = None
    ) -> None:
        if self._status != ExecutionStatus.EXECUTING:
            raise DomainError(f"Cannot fail execution in status {self._status!r}")
        if now is None:
            now = Timestamp.now()
        self._status = ExecutionStatus.FAILED
        self._error = ErrorDescription(error) if isinstance(error, str) else error
        self._completed_at = now
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            SchedulerExecutionFailedEvent(
                occurred_at=OccurredAt.from_datetime(now.value),
                execution_id=self.id,
            )
        )

    def skip(self, reason: Reason | str, now: Timestamp | None = None) -> None:
        if self._status != ExecutionStatus.PENDING:
            raise DomainError(f"Cannot skip execution in status {self._status!r}")
        if now is None:
            now = Timestamp.now()
        self._status = ExecutionStatus.SKIPPED
        self._completed_at = now
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            SchedulerExecutionSkippedEvent(
                occurred_at=OccurredAt.from_datetime(now.value),
                execution_id=self.id,
            )
        )
