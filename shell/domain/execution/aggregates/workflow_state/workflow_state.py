from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId
from shell.domain.execution.value_objects.state_data import StateData
from shell.domain.execution.value_objects.state_kind import StateKind
from shell.domain.platform.base.aggregate_root import AggregateRoot
from shell.domain.platform.value_objects.created_at import CreatedAt

if TYPE_CHECKING:
    from datetime import datetime
    from shell.domain.execution.aggregates.workflow_state.value_objects.workflow_state_id import (
        WorkflowStateId,
    )


class WorkflowState(AggregateRoot["WorkflowStateId"]):
    __slots__ = ("_workflow_id", "_kind", "_state_data", "_created_at")

    _workflow_id: WorkflowId
    _kind: StateKind
    _state_data: StateData
    _created_at: CreatedAt

    def __init__(
        self,
        *,
        id: WorkflowStateId,
        workflow_id: WorkflowId,
        kind: StateKind = StateKind.INPUT,
        state_data: StateData | None = None,
        created_at: CreatedAt | None = None,
    ) -> None:
        super().__init__(id)
        self._workflow_id = workflow_id
        self._kind = kind
        self._state_data = state_data or StateData({})
        if created_at is not None:
            self._created_at = created_at

    @classmethod
    def restore(
        cls,
        *,
        id: WorkflowStateId,
        workflow_id: WorkflowId,
        kind: StateKind = StateKind.INPUT,
        state_data: StateData | None = None,
        created_at: CreatedAt | None = None,
    ) -> Self:
        return cls(
            id=id,
            workflow_id=workflow_id,
            kind=kind,
            state_data=state_data,
            created_at=created_at,
        )

    @property
    def workflow_id(self) -> WorkflowId:
        return self._workflow_id

    @property
    def kind(self) -> StateKind:
        return self._kind

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
        kind: StateKind = StateKind.INPUT,
        payload: dict[str, object] | None = None,
        now: datetime,
    ) -> WorkflowState:
        instance = cls(
            id=id_,
            workflow_id=workflow_id,
            kind=kind,
            state_data=StateData(payload or {}),
            created_at=CreatedAt.from_datetime(now),
        )
        return instance

    def update(self, key: str, value: object) -> None:
        from shell.domain.execution.aggregates.workflow_state.events.workflow_state_changed_event import (
            WorkflowStateChangedEvent,
        )
        old_value = self._state_data.get(key)
        new_data = dict(self._state_data.to_dict())
        new_data[key] = value
        self._state_data = StateData(new_data)
        self.append_event(
            WorkflowStateChangedEvent.now(
                workflow_id=self._workflow_id,
                workflow_state_id=self.id,
                kind=self._kind,
                key=key,
                old_value=old_value,
                new_value=value,
                now=self._created_at,
            )
        )

    def get(self, key: str) -> object | None:
        return self._state_data.get(key)

    def delete(self, key: str) -> None:
        from shell.domain.execution.aggregates.workflow_state.events.workflow_state_changed_event import (
            WorkflowStateChangedEvent,
        )
        if self._state_data.get(key) is not None:
            old_value = self._state_data.get(key)
            new_data = dict(self._state_data.to_dict())
            new_data.pop(key, None)
            self._state_data = StateData(new_data)
            self.append_event(
                WorkflowStateChangedEvent.now(
                    workflow_id=self._workflow_id,
                    workflow_state_id=self.id,
                    kind=self._kind,
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
