from __future__ import annotations

import json
from typing import TYPE_CHECKING, Self

from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.state_data import StateData
from shell.platform.domain.value_objects.updated_at import UpdatedAt
from shell.platform.types import JsonStr  # noqa: TC001 -- potrzebny w runtime

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId
    from shell.domain.execution.aggregates.workflow_state.value_objects.workflow_state_id import (
        WorkflowStateId,
    )
    from shell.platform.domain.value_objects.deleted_at import DeletedAt
    from shell.platform.domain.value_objects.state_direction import StateDirection


from shell.domain.execution.aggregates.workflow_state.events.workflow_state_changed_event import (
    WorkflowStateChangedEvent,
)
from shell.domain.execution.aggregates.workflow_state.events.workflow_state_deleted_event import (
    WorkflowStateDeletedEvent,
)
from shell.domain.execution.aggregates.workflow_state.events.workflow_state_updated_event import (
    WorkflowStateUpdatedEvent,
)


class WorkflowState(AggregateRoot["WorkflowStateId"]):
    __slots__ = (
        "_updated_at",
        "_workflow_id",
        "_direction",
        "_state_data",
        "_created_at",
        "_deleted_at",
    )

    _workflow_id: WorkflowId
    _direction: StateDirection
    _state_data: StateData
    _created_at: CreatedAt
    _updated_at: UpdatedAt | None
    _deleted_at: DeletedAt | None

    def __init__(
        self,
        *,
        id: WorkflowStateId,
        workflow_id: WorkflowId,
        state_data: StateData,
        created_at: CreatedAt,
        direction: StateDirection,
    ) -> None:
        super().__init__(id)
        self._workflow_id = workflow_id
        self._direction = direction
        self._state_data = state_data
        self._created_at = created_at
        self._updated_at = None
        self._deleted_at = None

    @classmethod
    def create(
        cls,
        *,
        id_: WorkflowStateId,
        workflow_id: WorkflowId,
        direction: StateDirection,
        now: CreatedAt,
    ) -> WorkflowState:
        instance = cls(
            id=id_,
            workflow_id=workflow_id,
            direction=direction,
            state_data=StateData(JsonStr("{}")),
            created_at=now,
        )
        return instance

    def update(self, key: str, value: object) -> None:
        new_data = json.loads(self._state_data.value.value)
        new_data[key] = value
        self._state_data = StateData(JsonStr(json.dumps(new_data)))
        self.append_event(
            WorkflowStateChangedEvent.now(
                workflow_id=self._workflow_id,
                workflow_state_id=self.id,
                now=self._created_at,
            )
        )

    def get(self, key: str) -> object | None:
        return json.loads(self._state_data.value.value).get(key)  # type: ignore[no-any-return]

    def _remove_key(self, key: str) -> None:
        current = json.loads(self._state_data.value.value)
        if current.get(key) is not None:
            new_data = dict(current)
            new_data.pop(key, None)
            self._state_data = StateData(JsonStr(json.dumps(new_data)))
            self.append_event(
                WorkflowStateChangedEvent.now(
                    workflow_id=self._workflow_id,
                    workflow_state_id=self.id,
                    now=self._created_at,
                )
            )

    def patch(self, data: JsonStr) -> None:
        parsed = json.loads(data.value)
        for key, value in parsed.items():
            self.update(key, value)

    def clear(self) -> None:
        current = json.loads(self._state_data.value.value)
        for key in list(current.keys()):
            self._remove_key(key)

    def snapshot(self) -> StateData:
        return self._state_data

    @classmethod
    def restore(
        cls,
        *,
        id: WorkflowStateId,
        workflow_id: WorkflowId,
        state_data: StateData,
        created_at: CreatedAt,
        direction: StateDirection,
    ) -> Self:
        return cls(
            id=id,
            workflow_id=workflow_id,
            direction=direction,
            state_data=state_data,
            created_at=created_at,
        )

    def _update(self, now: UpdatedAt) -> None:
        self._updated_at = now
        self.append_event(
            WorkflowStateUpdatedEvent.now(
                workflow_state_id=self._id,
                now=CreatedAt.from_datetime(now.value),
            )
        )

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._updated_at = UpdatedAt.from_datetime(now.value)
        self.append_event(
            WorkflowStateDeletedEvent.now(
                workflow_state_id=self._id,
                now=CreatedAt.from_datetime(now.value),
            )
        )

    @property
    def workflow_id(self) -> WorkflowId:
        return self._workflow_id

    @property
    def direction(self) -> StateDirection:
        return self._direction

    @property
    def state_data(self) -> StateData:
        return self._state_data

    @property
    def created_at(self) -> CreatedAt:
        return self._created_at

    @classmethod
    def _new(
        cls,
        *,
        id_: WorkflowStateId,
        workflow_id: WorkflowId,
        direction: StateDirection,
        now: CreatedAt,
    ) -> WorkflowState:
        instance = cls(
            id=id_,
            workflow_id=workflow_id,
            direction=direction,
            state_data=StateData(JsonStr("{}")),
            created_at=now,
        )
        return instance
