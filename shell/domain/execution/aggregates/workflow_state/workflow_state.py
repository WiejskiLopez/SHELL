from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.state_data import StateData

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId
    from shell.domain.execution.aggregates.workflow_state.value_objects.workflow_state_id import (
        WorkflowStateId,
    )
    from shell.platform.domain.value_objects.state_direction import StateDirection


from shell.domain.execution.aggregates.workflow_state.events.workflow_state_changed_event import (
    WorkflowStateChangedEvent,
)


class WorkflowState(AggregateRoot["WorkflowStateId"]):
    __slots__ = ("_workflow_id", "_direction", "_state_data", "_created_at")

    _workflow_id: WorkflowId
    _direction: StateDirection
    _state_data: StateData
    _created_at: CreatedAt

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
    def create(
        cls,
        *,
        id_: WorkflowStateId,
        workflow_id: WorkflowId,
        direction: StateDirection,
        state_data: StateData,
        now: datetime,
    ) -> WorkflowState:
        instance = cls(
            id=id_,
            workflow_id=workflow_id,
            direction=direction,
            state_data=state_data,
            created_at=CreatedAt.from_datetime(now),
        )
        return instance

    def update(self, key: str, value: object) -> None:
        old_value = self._state_data.get(key)
        new_data = dict(self._state_data.to_dict())
        new_data[key] = value
        self._state_data = StateData(new_data)
        self.append_event(
            WorkflowStateChangedEvent.now(
                workflow_id=self._workflow_id,
                workflow_state_id=self.id,
                direction=self._direction,
                key=key,
                old_value=old_value,
                new_value=value,
                now=self._created_at,
            )
        )

    def get(self, key: str) -> object | None:
        return self._state_data.get(key)  # type: ignore[no-any-return]

    def delete(self, key: str) -> None:
        if self._state_data.get(key) is not None:
            old_value = self._state_data.get(key)
            new_data = dict(self._state_data.to_dict())
            new_data.pop(key, None)
            self._state_data = StateData(new_data)
            self.append_event(
                WorkflowStateChangedEvent.now(
                    workflow_id=self._workflow_id,
                    workflow_state_id=self.id,
                    direction=self._direction,
                    key=key,
                    old_value=old_value,
                    new_value=None,
                    now=self._created_at,
                )
            )

    def patch(self, data: dict[str, object]) -> None:
        for key, value in data.items():
            self.update(key, value)

    def clear(self) -> None:
        current = self._state_data.to_dict()
        for key in list(current.keys()):
            self.delete(key)

    def snapshot(self) -> StateData:
        return self._state_data
