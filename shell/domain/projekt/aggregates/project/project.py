from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.platform.base.aggregate_root import AggregateRoot
from shell.domain.projekt.aggregates.project.events.project_activated_event import (
    ProjectActivatedEvent,
)
from shell.domain.projekt.aggregates.project.events.project_archived_event import (
    ProjectArchivedEvent,
)
from shell.domain.projekt.aggregates.project.exceptions.invalid_project_transition import (
    InvalidProjectTransition,
)
from shell.domain.projekt.value_objects.project_id import ProjectId
from shell.domain.projekt.value_objects.project_status import ProjectStatus

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.projekt.aggregates.project.entities.project_skill import ProjectSkill
    from shell.domain.projekt.aggregates.project.entities.project_state_input import (
        ProjectStateInput,
    )
    from shell.domain.projekt.aggregates.project.entities.project_state_output import (
        ProjectStateOutput,
    )
    from shell.domain.projekt.value_objects.project_name import ProjectName
    from shell.domain.projekt.value_objects.repo_url import RepoUrl


class Project(AggregateRoot[ProjectId]):
    __slots__ = (
        "_name",
        "_repo_url",
        "_status",
        "_skills",
        "_state_inputs",
        "_state_outputs",
    )

    _name: ProjectName
    _repo_url: RepoUrl
    _status: ProjectStatus
    _skills: list[ProjectSkill]
    _state_inputs: list[ProjectStateInput]
    _state_outputs: list[ProjectStateOutput]

    def __init__(
        self,
        *,
        id: ProjectId,
        name: ProjectName,
        repo_url: RepoUrl,
        status: ProjectStatus = ProjectStatus.ACTIVE,
        skills: list[ProjectSkill] | None = None,
        state_inputs: list[ProjectStateInput] | None = None,
        state_outputs: list[ProjectStateOutput] | None = None,
    ) -> None:
        super().__init__(id)
        self._name = name
        self._repo_url = repo_url
        self._status = status
        self._skills = list(skills) if skills else []
        self._state_inputs = list(state_inputs) if state_inputs else []
        self._state_outputs = list(state_outputs) if state_outputs else []

    @property
    def name(self) -> ProjectName:
        return self._name

    @property
    def repo_url(self) -> RepoUrl:
        return self._repo_url

    @property
    def status(self) -> ProjectStatus:
        return self._status

    @property
    def skills(self) -> tuple[ProjectSkill, ...]:
        return tuple(self._skills)

    @property
    def state_inputs(self) -> tuple[ProjectStateInput, ...]:
        return tuple(self._state_inputs)

    @property
    def state_outputs(self) -> tuple[ProjectStateOutput, ...]:
        return tuple(self._state_outputs)

    def archive(self, now: datetime) -> None:
        if self._status != ProjectStatus.ACTIVE:
            raise InvalidProjectTransition(
                f"Cannot archive project in status {self._status!r}"
            )
        self._status = ProjectStatus.ARCHIVED
        self.append_event(ProjectArchivedEvent.now(self._id, now=now))

    def activate(self, now: datetime) -> None:
        if self._status != ProjectStatus.ARCHIVED:
            raise InvalidProjectTransition(
                f"Cannot activate project in status {self._status!r}"
            )
        self._status = ProjectStatus.ACTIVE
        self.append_event(ProjectActivatedEvent.now(self._id, now=now))
