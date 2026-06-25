"""Workflow aggregate root — V3 with FSM (ACTIVE -> COMPLETED | ABORTED)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.workflow.events.workflow_aborted_event import (
    WorkflowAbortedEvent,
)
from shell.domain.execution.aggregates.workflow.events.workflow_completed_event import (
    WorkflowCompletedEvent,
)
from shell.domain.execution.aggregates.workflow.events.workflow_skill_added_event import (
    WorkflowSkillAddedEvent,
)
from shell.domain.execution.aggregates.workflow.events.workflow_started_event import (
    WorkflowStartedEvent,
)
from shell.domain.execution.aggregates.workflow.events.workflow_state_input_added_event import (
    WorkflowStateInputAddedEvent,
)
from shell.domain.execution.aggregates.workflow.events.workflow_state_output_added_event import (
    WorkflowStateOutputAddedEvent,
)
from shell.domain.execution.aggregates.workflow.exceptions.invalid_workflow_transition import (
    InvalidWorkflowTransition,
)
from shell.domain.execution.value_objects.workflow_status import WorkflowStatus
from shell.domain.platform.base import AggregateRoot

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.session.value_objects.session_id import SessionId
    from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
        TaskExecutionId,
    )
    from shell.domain.execution.aggregates.workflow.entities.workflow_skill import (
        WorkflowSkill,
    )
    from shell.domain.execution.aggregates.workflow.entities.workflow_state_input import (
        WorkflowStateInput,
    )
    from shell.domain.execution.aggregates.workflow.entities.workflow_state_output import (
        WorkflowStateOutput,
    )
    from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId
    from shell.domain.execution.value_objects.skill_payload import SkillPayload


class Workflow(AggregateRoot["WorkflowId"]):
    __slots__ = (
        "_session_id",
        "_status",
        "_created_at",
        "_skills",
        "_state_inputs",
        "_state_outputs",
    )

    _session_id: SessionId
    _status: WorkflowStatus
    _created_at: datetime
    _skills: list[WorkflowSkill]
    _state_inputs: list[WorkflowStateInput]
    _state_outputs: list[WorkflowStateOutput]

    def __init__(
        self,
        *,
        id: WorkflowId,
        session_id: SessionId | None = None,
        status: WorkflowStatus | None = None,
        created_at: datetime | None = None,
        skills: list[WorkflowSkill] | None = None,
        state_inputs: list[WorkflowStateInput] | None = None,
        state_outputs: list[WorkflowStateOutput] | None = None,
    ) -> None:
        super().__init__(id)
        self._session_id = session_id or None  # type: ignore[assignment]
        self._status = status or WorkflowStatus.ACTIVE
        self._created_at = created_at or datetime.min
        self._skills = skills or []
        self._state_inputs = state_inputs or []
        self._state_outputs = state_outputs or []

    # --- Properties ---

    @property
    def session_id(self) -> SessionId | None:
        return self._session_id

    @property
    def status(self) -> WorkflowStatus:
        return self._status

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def skills(self) -> list:
        return self._skills

    @property
    def state_inputs(self) -> list:
        return self._state_inputs

    @property
    def state_outputs(self) -> list:
        return self._state_outputs

    # --- Factory ---

    @classmethod
    def new(
        cls,
        *,
        id_: WorkflowId,
        now: datetime,
        session_id: SessionId | None = None,
    ) -> Workflow:
        return cls(
            id=id_,
            session_id=session_id,
            status=WorkflowStatus.ACTIVE,
            created_at=now,
        )

    # --- Methods ---

    def start_at(
        self,
        *,
        now: datetime,
        task_execution_id: TaskExecutionId | None = None,
    ) -> None:
        if self._status != WorkflowStatus.ACTIVE:
            raise InvalidWorkflowTransition(
                f"start_at requires status=ACTIVE, got {self._status.value!r}"
            )
        self.append_event(
            WorkflowStartedEvent.now(self.id, now=now, task_execution_id=task_execution_id)
        )

    def finish(
        self,
        now: datetime | None = None,
        task_execution_id: TaskExecutionId | None = None,
    ) -> None:
        if self._status != WorkflowStatus.ACTIVE:
            raise InvalidWorkflowTransition(
                f"finish requires status=ACTIVE, got {self._status.value!r}"
            )
        self._status = WorkflowStatus.COMPLETED
        self.append_event(
            WorkflowCompletedEvent.now(self.id, now=now, task_execution_id=task_execution_id)
        )

    def abort(
        self,
        *,
        reason: str | None = None,
        now: datetime,
        task_execution_id: TaskExecutionId | None = None,
    ) -> None:
        if self._status != WorkflowStatus.ACTIVE:
            raise InvalidWorkflowTransition(
                f"abort requires status=ACTIVE, got {self._status.value!r}"
            )
        self._status = WorkflowStatus.ABORTED
        self.append_event(
            WorkflowAbortedEvent.now(self.id, now=now, task_execution_id=task_execution_id)
        )

    def add_skill(self, payload: SkillPayload, now: datetime) -> None:
        from shell.domain.execution.aggregates.workflow.entities.workflow_skill import (
            WorkflowSkill,
        )
        from shell.domain.execution.aggregates.workflow.value_objects.workflow_skill_id import (
            WorkflowSkillId,
        )

        skill = WorkflowSkill(
            id=WorkflowSkillId.generate(),
            workflow_id=self._id,
            payload=payload,
            created_at=now,
        )
        self._skills.append(skill)
        self.append_event(WorkflowSkillAddedEvent.now(self._id, skill.id, now=now))

    def add_state_input(self, payload: dict, now: datetime) -> None:
        from shell.domain.execution.aggregates.workflow.entities.workflow_state_input import (
            WorkflowStateInput,
        )
        state = WorkflowStateInput(
            id=self.id,
            workflow_id=self.id,
            payload=payload,
            created_at=now,
        )
        self._state_inputs.append(state)
        self.append_event(WorkflowStateInputAddedEvent.now(self.id, now=now))

    def add_state_output(self, payload: dict, now: datetime) -> None:
        from shell.domain.execution.aggregates.workflow.entities.workflow_state_output import (
            WorkflowStateOutput,
        )
        state = WorkflowStateOutput(
            id=self.id,
            workflow_id=self.id,
            payload=payload,
            created_at=now,
        )
        self._state_outputs.append(state)
        self.append_event(WorkflowStateOutputAddedEvent.now(self.id, now=now))
