"""ProjectState — external input/output state for a project, a separate AggregateRoot.

Consolidates ProjectStateInput and ProjectStateOutput into a single aggregate
with a ``direction`` discriminator (StateDirection.IN or StateDirection.OUT).

INPUT state represents data fed into the project from external sources.
OUTPUT state represents data produced during project operations.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Self

from shell.platform.domain.base import AggregateRoot
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import NONE_DELETED_AT, DeletedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.domain.value_objects.state_data import StateData
from shell.platform.domain.value_objects.updated_at import NONE_UPDATED_AT, UpdatedAt
from shell.platform.types import JsonStr  # noqa: TC001 -- potrzebny w runtime
from shell.project_service.domain.project.aggregates.project_state.events.project_state_changed_event import (
    ProjectStateChangedEvent,
)
from shell.project_service.domain.project.aggregates.project_state.events.project_state_deleted_event import (
    ProjectStateDeletedEvent,
)
from shell.project_service.domain.project.aggregates.project_state.events.project_state_updated_event import (
    ProjectStateUpdatedEvent,
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
        "_updated_at",
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
        updated_at: UpdatedAt = NONE_UPDATED_AT,
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
        self._updated_at = updated_at
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
        return cls(
            id=id_,
            project_id=project_id,
            direction=direction,
            state_data=StateData(JsonStr("{}")),
            created_at=CreatedAt.from_datetime(now.value),
        )

    # ------------------------------------------------------------------ mutations

    def set_key(self, key: str, value: object) -> None:
        new_data = json.loads(self._state_data.value.value)
        new_data[key] = value
        self._state_data = StateData(JsonStr(json.dumps(new_data)))
        self.append_event(
            ProjectStateChangedEvent.now(
                project_id=self._project_id,
                project_state_id=self.id,
                now=OccurredAt.from_datetime(self._created_at.value),
            )
        )

    def get(self, key: str) -> object | None:
        result: object | None = json.loads(self._state_data.value.value).get(key)
        return result

    def remove_key(self, key: str) -> None:
        if json.loads(self._state_data.value.value).get(key) is not None:
            new_data = json.loads(self._state_data.value.value)
            new_data.pop(key, None)
            self._state_data = StateData(JsonStr(json.dumps(new_data)))
            self.append_event(
                ProjectStateChangedEvent.now(
                    project_id=self._project_id,
                    project_state_id=self.id,
                    now=OccurredAt.from_datetime(self._created_at.value),
                )
            )

    def patch(self, data: JsonStr) -> None:
        parsed = json.loads(data.value)
        for key, value in parsed.items():
            self.set_key(key, value)

    def clear(self) -> None:
        current = json.loads(self._state_data.value.value)
        for key in list(current.keys()):
            self.remove_key(key)

    def merge(self, other: ProjectState) -> None:
        other_data = json.loads(other._state_data.value.value)
        current = json.loads(self._state_data.value.value)
        for key, value in other_data.items():
            if key not in current:
                self.set_key(key, value)

    def snapshot(self) -> StateData:
        return self._state_data

    @classmethod
    def restore(
        cls,
        *,
        id: ProjectStateId,
        created_at: CreatedAt,
        updated_at: UpdatedAt = NONE_UPDATED_AT,
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
            updated_at=updated_at,
            deleted_at=deleted_at,
        )

    # ------------------------------------------------------------------ properties

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._updated_at = UpdatedAt.from_datetime(now.value)
        self.append_event(
            ProjectStateDeletedEvent.now(
                project_state_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def _update(self, now: UpdatedAt) -> None:
        self._updated_at = now
        self.append_event(
            ProjectStateUpdatedEvent.now(
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
    def updated_at(self) -> UpdatedAt:
        return self._updated_at

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
        return cls(
            id=id_,
            project_id=project_id,
            direction=direction,
            state_data=StateData(JsonStr("{}")),
            created_at=CreatedAt.from_datetime(now.value),
        )
