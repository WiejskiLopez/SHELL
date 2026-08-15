"""ProjectState — external input/output state for a project, a separate AggregateRoot.

Consolidates ProjectStateInput and ProjectStateOutput into a single aggregate
with a ``direction`` discriminator (StateDirection.IN or StateDirection.OUT).

INPUT state represents data fed into the project from external sources.
OUTPUT state represents data produced during project operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.platform.domain.base import AggregateRoot
from shell.platform.domain.exceptions.domain_error import DomainError
from shell.platform.domain.value_objects.changed_at import NONE_CHANGED_AT, ChangedAt
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import NONE_DELETED_AT, DeletedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.domain.value_objects.state_data import StateData
from shell.platform.types import JsonStr  # noqa: TC001 -- potrzebny w runtime
from shell.project_service.domain.project.aggregates.project_state.events.project_state_changed_event import (
    ProjectStateChangedEvent,
)
from shell.project_service.domain.project.aggregates.project_state.events.project_state_created_event import (
    ProjectStateCreatedEvent,
)
from shell.project_service.domain.project.aggregates.project_state.events.project_state_deleted_event import (
    ProjectStateDeletedEvent,
)
from shell.project_service.domain.project.aggregates.project_state.value_objects.project_state_id import (
    ProjectStateId,
)

if TYPE_CHECKING:
    from shell.platform.domain.value_objects.state_direction import StateDirection
    from shell.project_service.domain.project.aggregates.project.value_objects.project_id import (
        ProjectId,
    )


class ProjectState(AggregateRoot[ProjectStateId]):
    __slots__ = (
        "_created_at",
        "_changed_at",
        "_deleted_at",
        "_project_id",
        "_direction",
        "_state_data",
    )

    _project_id: ProjectId
    _direction: StateDirection
    _state_data: StateData

    def __init__(
        self,
        *,
        id: ProjectStateId,
        created_at: CreatedAt,
        changed_at: ChangedAt = NONE_CHANGED_AT,
        deleted_at: DeletedAt = NONE_DELETED_AT,
        project_id: ProjectId,
        direction: StateDirection,
        state_data: StateData,
    ) -> None:
        super().__init__(id)
        self._project_id = project_id
        self._direction = direction
        self._state_data = state_data
        self._created_at = created_at
        self._changed_at = changed_at
        self._deleted_at = deleted_at

    @classmethod
    def create(
        cls,
        *,
        id_: ProjectStateId,
        now: CreatedAt,
        project_id: ProjectId,
        direction: StateDirection,
    ) -> ProjectState:
        return cls._new(
            id_=id_,
            project_id=project_id,
            direction=direction,
            now=OccurredAt.from_datetime(now.value),
        )

    # ------------------------------------------------------------------ mutations

    def change_state(self, state_data: StateData) -> None:
        if self._deleted_at.value is not None:
            raise DomainError("Cannot change state of a deleted project state")
        self._state_data = state_data
        self._change(now=OccurredAt.from_datetime(self._created_at.value))

    def snapshot(self) -> StateData:
        return self._state_data

    @classmethod
    def restore(
        cls,
        *,
        id: ProjectStateId,
        created_at: CreatedAt,
        changed_at: ChangedAt = NONE_CHANGED_AT,
        deleted_at: DeletedAt = NONE_DELETED_AT,
        project_id: ProjectId,
        direction: StateDirection,
        state_data: StateData,
    ) -> Self:
        return cls(
            id=id,
            project_id=project_id,
            direction=direction,
            state_data=state_data,
            created_at=created_at,
            changed_at=changed_at,
            deleted_at=deleted_at,
        )

    # ------------------------------------------------------------------ properties

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            ProjectStateDeletedEvent.now(
                project_state_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def _change(self, now: OccurredAt) -> None:
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            ProjectStateChangedEvent.now(
                project_id=self._project_id,
                project_state_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    @property
    def project_id(self) -> ProjectId:
        return self._project_id

    @property
    def direction(self) -> StateDirection:
        return self._direction

    @property
    def state_data(self) -> StateData:
        return self._state_data

    @property
    def created_at(self) -> CreatedAt:
        return self._created_at

    @property
    def changed_at(self) -> ChangedAt:
        return self._changed_at

    @property
    def deleted_at(self) -> DeletedAt:
        return self._deleted_at

    # ------------------------------------------------------------------ factory

    @classmethod
    def _new(
        cls,
        *,
        id_: ProjectStateId,
        now: OccurredAt,
        project_id: ProjectId,
        direction: StateDirection,
    ) -> ProjectState:
        instance = cls(
            id=id_,
            project_id=project_id,
            direction=direction,
            state_data=StateData(JsonStr("{}")),
            created_at=CreatedAt.from_datetime(now.value),
        )
        instance.append_event(
            ProjectStateCreatedEvent.now(
                project_id=project_id,
                project_state_id=id_,
                now=OccurredAt.from_datetime(now.value),
            )
        )
        return instance
