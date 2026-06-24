"""Session aggregate root — V3 with FSM (OPEN -> CLOSED) and skills."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.session.events.session_opened_event import (
    SessionOpenedEvent,
)
from shell.domain.execution.aggregates.session.value_objects.session_id import SessionId
from shell.domain.execution.value_objects.environment import Environment
from shell.domain.execution.value_objects.session_status import SessionStatus
from shell.domain.platform.base.aggregate_root import AggregateRoot
from shell.domain.projekt.value_objects.project_id import ProjectId
from shell.domain.user.value_objects.user_id import UserId

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.execution.aggregates.session.entities.session_skill import SessionSkill
    from shell.domain.execution.aggregates.session.entities.session_state_input import (
        SessionStateInput,
    )
    from shell.domain.execution.aggregates.session.value_objects.session_skill_id import SessionSkillId
    from shell.domain.execution.value_objects.skill_payload import SkillPayload
    from shell.domain.execution.aggregates.session.entities.session_state_output import (
        SessionStateOutput,
    )


class Session(AggregateRoot[SessionId]):
    """Session aggregate root — V3 with FSM (OPEN -> CLOSED)."""

    __slots__ = (
        "_user_id",
        "_project_id",
        "_environment",
        "_status",
        "_opened_at",
        "_closed_at",
        "_skills",
        "_state_inputs",
        "_state_outputs",
    )

    _user_id: UserId
    _project_id: ProjectId
    _environment: Environment
    _status: SessionStatus
    _opened_at: datetime
    _closed_at: datetime | None
    _skills: list[SessionSkill]
    _state_inputs: list[SessionStateInput]
    _state_outputs: list[SessionStateOutput]

    def __init__(
        self,
        *,
        id: SessionId,
        user_id: UserId,
        project_id: ProjectId,
        environment: Environment,
        status: SessionStatus,
        opened_at: datetime,
        closed_at: datetime | None = None,
        skills: list[SessionSkill] | None = None,
        state_inputs: list[SessionStateInput] | None = None,
        state_outputs: list[SessionStateOutput] | None = None,
    ) -> None:
        super().__init__(id)
        self._user_id = user_id
        self._project_id = project_id
        self._environment = environment
        self._status = status
        self._opened_at = opened_at
        self._closed_at = closed_at
        self._skills = skills or []
        self._state_inputs = state_inputs or []
        self._state_outputs = state_outputs or []

    # --- V3 properties ---

    @property
    def user_id(self) -> UserId:
        return self._user_id

    @property
    def project_id(self) -> ProjectId:
        return self._project_id

    @property
    def environment(self) -> Environment:
        return self._environment

    @property
    def session_status(self) -> SessionStatus:
        return self._status

    @property
    def opened_at(self) -> datetime:
        return self._opened_at

    @property
    def closed_at(self) -> datetime | None:
        return self._closed_at

    @property
    def skills(self) -> list[SessionSkill]:
        return self._skills

    @property
    def state_inputs(self) -> list[SessionStateInput]:
        return self._state_inputs

    @property
    def state_outputs(self) -> list[SessionStateOutput]:
        return self._state_outputs

    # --- Legacy deprecated properties ---

    @property
    def goal(self) -> str:
        """Deprecated: goal was replaced by structured state_inputs."""
        return ""

    @property
    def status(self) -> str:
        """Returns lowercase status string for backward compat."""
        return self._status.value.lower()

    @property
    def session_status(self) -> SessionStatus:
        return self._status

    # --- Factory ---

    @classmethod
    def open(
        cls,
        id_: SessionId,
        user_id: UserId | None = None,
        project_id: ProjectId | None = None,
        environment: Environment | None = None,
        now: datetime | None = None,
        goal: str | None = None,  # legacy
    ) -> Session:
        if user_id is None:
            user_id = UserId.generate()
        if project_id is None:
            project_id = ProjectId.generate()
        if environment is None:
            environment = Environment(os="", runtime="", cwd="")
        if now is None:
            from datetime import datetime as _dt
            now = _dt.now()
        session = cls(
            id=id_,
            user_id=user_id,
            project_id=project_id,
            environment=environment,
            status=SessionStatus.OPEN,
            opened_at=now,
        )
        session.append_event(SessionOpenedEvent.now(session.id, user_id, project_id, now=now))
        return session

    # --- Methods ---

    def add_skill(self, payload: SkillPayload, now: datetime) -> None:
        from shell.domain.execution.aggregates.session.entities.session_skill import (
            SessionSkill,
        )
        from shell.domain.execution.aggregates.session.value_objects.session_skill_id import SessionSkillId

        skill = SessionSkill(
            id=SessionSkillId.generate(),
            session_id=self._id,
            payload=payload,
            created_at=now,
        )
        self._skills.append(skill)

    def close(self, now: datetime) -> None:
        if self._status != SessionStatus.OPEN:
            raise ValueError("Session already closed")
        self._status = SessionStatus.CLOSED
        self._closed_at = now
        from shell.domain.execution.aggregates.session.events.session_closed_event import (
            SessionClosedEvent,
        )
        self.append_event(SessionClosedEvent.now(self._id, now=now))
