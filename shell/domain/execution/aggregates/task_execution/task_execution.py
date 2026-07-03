from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

from shell.domain.execution.aggregates.task_execution.exceptions.invalid_task_state_error import (
    InvalidTaskStateError,
)
from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)
from shell.domain.execution.value_objects.max_planning_cycles import MaxPlanningCycles
from shell.domain.execution.value_objects.planning_cycle import PlanningCycle
from shell.domain.execution.value_objects.task_execution_name import TaskExecutionName
from shell.domain.execution.value_objects.task_execution_status import TaskExecutionStatus
from shell.domain.execution.value_objects.task_name import TaskName
from shell.domain.execution.value_objects.work_dir import WorkDir
from shell.domain.platform.base.aggregate_root import AggregateRoot
from shell.domain.platform.value_objects.created_at import CreatedAt

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId
    from shell.domain.execution.value_objects.reason import Reason
    from shell.domain.execution.value_objects.task_execution_body import TaskExecutionBody


from shell.domain.execution.aggregates.task_execution.events.task_execution_created_event import (
            TaskExecutionCreatedEvent,
        )
from shell.domain.execution.aggregates.task_execution.events.task_execution_exhausted_event import (
            TaskExecutionExhaustedEvent,
        )
from shell.domain.execution.aggregates.task_execution.events.task_execution_timeout_expired_event import (
            TaskExecutionTimeoutExpiredEvent,
        )
from shell.domain.execution.aggregates.task_execution.events.task_execution_failed_event import (
            TaskExecutionFailedEvent,
        )
from shell.domain.execution.aggregates.task_execution.events.task_execution_completed_event import (
            TaskExecutionCompletedEvent,
        )
from shell.domain.execution.aggregates.task_execution.events.task_execution_started_event import (
            TaskExecutionStartedEvent,
        )
class TaskExecution(AggregateRoot[TaskExecutionId]):
    __slots__ = (
        "_workflow_id",
        "_status",
        "_max_planning_cycles",
        "_current_cycle",
        "_name",
        "_body",
        "_work_dir",
        "_created_at",
    )

    def __init__(
        self,
        id: TaskExecutionId,
        name: TaskName | None = None,
        body: TaskExecutionBody | None = None,
        workflow_id: WorkflowId | None = None,
        max_planning_cycles: MaxPlanningCycles | None = None,
        work_dir: WorkDir | None = None,
        created_at: CreatedAt | None = None,
    ) -> None:
        super().__init__(id)
        self._workflow_id = workflow_id
        self._status = TaskExecutionStatus.CREATED
        self._max_planning_cycles = max_planning_cycles or MaxPlanningCycles(5)
        self._current_cycle = PlanningCycle(0)
        self._name = name if name is not None else TaskName("default")
        self._body = body
        self._work_dir = work_dir if work_dir is not None else WorkDir("/tmp")
        self._created_at = created_at

    @classmethod
    def restore(
        cls,
        id: TaskExecutionId,
        name: TaskName | None = None,
        body: TaskExecutionBody | None = None,
        workflow_id: WorkflowId | None = None,
        max_planning_cycles: MaxPlanningCycles | None = None,
        work_dir: WorkDir | None = None,
        created_at: CreatedAt | None = None,
    ) -> Self:
        return cls(
            id=id,
            name=name,
            body=body,
            workflow_id=workflow_id,
            max_planning_cycles=max_planning_cycles,
            work_dir=work_dir,
            created_at=created_at,
        )

    # --- V3 FSM ---

    def start(self, now: datetime) -> None:
        if self._status != TaskExecutionStatus.CREATED:
            raise InvalidTaskStateError(f"Cannot start task in status {self._status}")
        self._status = TaskExecutionStatus.IN_PROGRESS
        self.append_event(
            TaskExecutionStartedEvent.now(
                task_execution_id=self._id,
                now=CreatedAt.from_datetime(now),
            )
        )

    def complete(self, output: str = "", now: datetime | None = None) -> None:
        if self._status != TaskExecutionStatus.IN_PROGRESS:
            raise InvalidTaskStateError(f"Cannot complete task in status {self._status}")
        self._status = TaskExecutionStatus.COMPLETED
        self.append_event(
            TaskExecutionCompletedEvent.now(
                task_execution_id=self._id,
                task_execution_name=TaskExecutionName(self._name.value),
                output=output,
                now=CreatedAt.from_datetime(now) if now is not None else None,
            )
        )

    def fail(self, reason: Reason, now: datetime) -> None:
        if self._status != TaskExecutionStatus.IN_PROGRESS:
            raise InvalidTaskStateError(f"Cannot fail task in status {self._status}")
        self._status = TaskExecutionStatus.FAILED
        self.append_event(
            TaskExecutionFailedEvent.now(
                task_execution_id=self._id,
                reason=reason,
                now=CreatedAt.from_datetime(now),
            )
        )

    def timeout(self, now: datetime) -> None:
        if self._status != TaskExecutionStatus.IN_PROGRESS:
            raise InvalidTaskStateError(f"Cannot timeout task in status {self._status}")
        self._status = TaskExecutionStatus.TIMED_OUT
        self.append_event(
            TaskExecutionTimeoutExpiredEvent.now(
                task_execution_id=self._id,
                now=CreatedAt.from_datetime(now),
            )
        )

    def exhaust(self, now: datetime) -> None:
        if self._status != TaskExecutionStatus.IN_PROGRESS:
            raise InvalidTaskStateError(f"Cannot exhaust task in status {self._status}")
        self._status = TaskExecutionStatus.EXHAUSTED
        self.append_event(
            TaskExecutionExhaustedEvent.now(
                task_execution_id=self._id,
                current_cycle=self._current_cycle,
                max_planning_cycles=self._max_planning_cycles,
                now=CreatedAt.from_datetime(now),
            )
        )

    def increment_cycle(self) -> bool:
        if self._current_cycle.value >= self._max_planning_cycles.value:
            return False
        self._current_cycle = PlanningCycle(self._current_cycle.value + 1)
        return True

    # --- Properties ---

    @property
    def name(self) -> TaskName:
        return self._name

    @property
    def status(self) -> TaskExecutionStatus:
        return self._status

    @property
    def max_planning_cycles(self) -> MaxPlanningCycles:
        return self._max_planning_cycles

    @property
    def current_cycle(self) -> PlanningCycle:
        return self._current_cycle

    @property
    def body(self) -> TaskExecutionBody | None:
        return self._body

    @property
    def work_dir(self) -> WorkDir:
        return self._work_dir

    @property
    def workflow_id(self) -> WorkflowId | None:
        return self._workflow_id

    @property
    def created_at(self) -> CreatedAt | None:
        return self._created_at

    def rename(self, new_name: TaskName) -> None:
        self._name = new_name

    def execute_in_workflow(self, workflow_id: WorkflowId) -> None:
        self._workflow_id = workflow_id

    def prepare_workspace(self, path: str) -> None:
        self._work_dir = WorkDir(path)

    @classmethod
    def create(
        cls,
        *,
        id_: TaskExecutionId,
        name: Any,
        now: datetime,
        body: TaskExecutionBody | None = None,
        workflow_id: WorkflowId | None = None,
    ) -> TaskExecution:
        task_name = name if isinstance(name, TaskName) else TaskName(str(name))
        task_execution = cls(
            id=id_,
            name=task_name,
            body=body,
            workflow_id=workflow_id,
            created_at=CreatedAt.from_datetime(now),
        )
        task_execution.append_event(
            TaskExecutionCreatedEvent.now(
                task_execution_id=id_,
                task_execution_name=TaskExecutionName(task_name.value),
                now=CreatedAt.from_datetime(now),
            )
        )
        return task_execution

