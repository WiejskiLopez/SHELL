"""ProjectState — external input/output state for a project, a separate AggregateRoot.

Consolidates ProjectStateInput and ProjectStateOutput into a single aggregate
with a ``direction`` discriminator (StateDirection.IN or StateDirection.OUT).

INPUT state represents data fed into the project from external sources.
OUTPUT state represents data produced during project operations.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

from shell.domain.platform.base import AggregateRoot
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.state_data import StateData
from shell.domain.platform.value_objects.state_direction import StateDirection
from shell.domain.project.aggregates.project_state.events.project_state_changed_event import (
    ProjectStateChangedEvent,
)
from shell.domain.project.aggregates.project_state.value_objects.project_state_id import (
    ProjectStateId,
)

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.project.value_objects.project_id import ProjectId


from shell.domain.platform.value_objects.deleted_at import DeletedAt
from shell.domain.platform.value_objects.updated_at import UpdatedAt


class ProjectState(AggregateRoot[ProjectStateId]):
    __slots__ = (
        "_project_id",
        "_direction",
        "_state_data",
        "_is_current",
        "_created_at",
        "_updated_at",
        "_deleted_at",
    )

    _project_id: ProjectId
    _direction: StateDirection
    _state_data: StateData
    _is_current: bool

    def __init__(
        self,
        *,
        id: ProjectStateId,
        project_id: ProjectId,
        direction: StateDirection,
        is_current: bool,
        state_data: StateData | None = None,
        created_at: CreatedAt | None = None,
        updated_at: UpdatedAt | None = None,
        deleted_at: DeletedAt | None = None,
    ) -> None:
        super().__init__(id)
        self._project_id = project_id
        self._direction = direction
        self._state_data = state_data or StateData({})
        self._is_current = is_current
        self._created_at = created_at
        self._updated_at = updated_at
        self._deleted_at = deleted_at

    @classmethod
    def restore(
        cls,
        *,
        id: ProjectStateId,
        project_id: ProjectId,
        direction: StateDirection,
        is_current: bool,
        state_data: StateData | None = None,
        created_at: CreatedAt | None = None,
        updated_at: UpdatedAt | None = None,
        deleted_at: DeletedAt | None = None,
    ) -> Self:
        return cls(
            id=id,
            project_id=project_id,
            direction=direction,
            state_data=state_data,
            is_current=is_current,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
        )

    # ------------------------------------------------------------------ properties

    @property
    def project_id(self) -> ProjectId:
        return self._project_id

    @property
    def direction(self) -> StateDirection:
        return self._direction

    @property
    def state_data(self) -> dict[str, Any]:
        return self._state_data.to_dict().copy()

    @property
    def is_current(self) -> bool:
        return self._is_current

    @property
    def created_at(self) -> CreatedAt | None:
        return self._created_at

    @property
    def updated_at(self) -> UpdatedAt | None:
        return self._updated_at

    @property
    def deleted_at(self) -> DeletedAt | None:
        return self._deleted_at

    # ------------------------------------------------------------------ factory

    @classmethod
    def create(
        cls,
        *,
        id_: ProjectStateId,
        project_id: ProjectId,
        direction: StateDirection = StateDirection.IN,
        now: CreatedAt | None = None,
    ) -> ProjectState:
        actual_now = now or CreatedAt.now()
        return cls(
            id=id_,
            project_id=project_id,
            direction=direction,
            state_data=StateData({}),
            is_current=True,
            created_at=actual_now,
        )

    # ------------------------------------------------------------------ mutations

    def set_key(self, key: str, value: object) -> None:
        old_value = self._state_data.get(key)
        new_data = dict(self._state_data.to_dict())
        new_data[key] = value
        self._state_data = StateData(new_data)
        actual_now = self._created_at or CreatedAt.now()
        self.append_event(
            ProjectStateChangedEvent.now(
                project_id=self._project_id,
                project_state_id=self.id,
                direction=self._direction,
                key=key,
                old_value=old_value,
                new_value=value,
                now=actual_now,
            )
        )

    def get(self, key: str) -> object | None:
        result: object | None = self._state_data.get(key)
        return result

    def remove_key(self, key: str) -> None:
        if self._state_data.get(key) is not None:
            old_value = self._state_data.get(key)
            new_data = dict(self._state_data.to_dict())
            new_data.pop(key, None)
            self._state_data = StateData(new_data)
            actual_now = self._created_at or CreatedAt.now()
            self.append_event(
                ProjectStateChangedEvent.now(
                    project_id=self._project_id,
                    project_state_id=self.id,
                    direction=self._direction,
                    key=key,
                    old_value=old_value,
                    new_value=None,
                    now=actual_now,
                )
            )

    def patch(self, data: dict[str, object]) -> None:
        for key, value in data.items():
            self.set_key(key, value)

    def clear(self) -> None:
        current = self._state_data.to_dict()
        for key in list(current.keys()):
            self.remove_key(key)

    def merge(self, other: ProjectState) -> None:
        other_data = other._state_data.to_dict()
        current = self._state_data.to_dict()
        for key, value in other_data.items():
            if key not in current:
                self.set_key(key, value)

    def snapshot(self) -> dict[str, Any]:
        return self._state_data.to_dict().copy()

    def supersede(self) -> None:
        self._is_current = False
