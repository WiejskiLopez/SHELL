from __future__ import annotations

import json
from typing import TYPE_CHECKING, Self

from shell.domain.execution.aggregates.node_execution_state.events.node_execution_state_changed_event import (
    NodeExecutionStateChangedEvent,
)
from shell.domain.execution.aggregates.node_execution_state.value_objects.node_execution_state_id import (
    NodeExecutionStateId,
)
from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.value_objects.state_data import StateData
from shell.platform.types import JsonStr  # noqa: TC001 -- potrzebny w runtime
from shell.platform.domain.value_objects.deleted_at import DeletedAt
from shell.platform.domain.value_objects.updated_at import UpdatedAt
from execution.aggregates.node_execution_state.events.nodeexecutionstate_updated_event import NodeExecutionStateUpdatedEvent
from execution.aggregates.node_execution_state.events.nodeexecutionstate_deleted_event import NodeExecutionStateDeletedEvent

from shell.platform.domain.value_objects.deletedat import DeletedAt

from shell.platform.domain.value_objects.updatedat import UpdatedAt

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )
    from shell.platform.domain.value_objects.created_at import CreatedAt
    from shell.platform.domain.value_objects.state_direction import StateDirection


class NodeExecutionState(AggregateRoot[NodeExecutionStateId]):
    __slots__ = (
        "_updated_at","_node_execution_id", "_direction", "_state_data", "_created_at")

    _node_execution_id: NodeExecutionId
    _direction: StateDirection
    _state_data: StateData
    _created_at: CreatedAt

    def __init__(
        self,
        id: NodeExecutionStateId,
        node_execution_id: NodeExecutionId,
        state_data: StateData,
        created_at: CreatedAt,
        direction: StateDirection,
    ) -> None:
        super().__init__(id)
        self._node_execution_id = node_execution_id
        self._direction = direction
        self._state_data = state_data
        self._created_at = created_at

    @classmethod
    def create(
        cls,
        *,
        id_: NodeExecutionStateId,
        node_execution_id: NodeExecutionId,
        direction: StateDirection,
        now: CreatedAt,
    ) -> NodeExecutionState:
        instance = cls(
            id=id_,
            node_execution_id=node_execution_id,
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
            NodeExecutionStateChangedEvent.now(
                node_execution_id=self._node_execution_id,
                node_execution_state_id=self.id,
                now=self._created_at,
            )
        )

    def get(self, key: str) -> object | None:
        return json.loads(self._state_data.value.value).get(key)  # type: ignore[no-any-return]

    def _delete(self, key: str) -> None:
        if json.loads(self._state_data.value.value).get(key) is not None:
            new_data = json.loads(self._state_data.value.value)
            new_data.pop(key, None)
            self._state_data = StateData(JsonStr(json.dumps(new_data)))
            self.append_event(
                NodeExecutionStateChangedEvent.now(
                    node_execution_id=self._node_execution_id,
                    node_execution_state_id=self.id,
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
            self.delete(key)

    def snapshot(self) -> StateData:
        return self._state_data

    @classmethod
    def restore(
        cls,
        id: NodeExecutionStateId,
        node_execution_id: NodeExecutionId,
        state_data: StateData,
        created_at: CreatedAt,
        direction: StateDirection,
    ) -> Self:
        return cls(
            id=id,
            node_execution_id=node_execution_id,
            direction=direction,
            state_data=state_data,
            created_at=created_at,
        )


    @classmethod
    def _update(cls) -> None:
        raise NotImplementedError("_update() not yet implemented")




    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._updated_at = UpdatedAt.from_datetime(now.value)
        self.append_event(
            NodeExecutionStateDeletedEvent.now(
                nodeexecutionstate_id=self._id,
                now=now,
            )
        )

    def _update(self, now: UpdatedAt) -> None:
        self._updated_at = now
        self.append_event(
            NodeExecutionStateUpdatedEvent.now(
                nodeexecutionstate_id=self._id,
                now=now,
            )
        )

    @property
    def node_execution_id(self) -> NodeExecutionId:
        return self._node_execution_id

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
        id_: NodeExecutionStateId,
        node_execution_id: NodeExecutionId,
        direction: StateDirection,
        now: CreatedAt,
    ) -> NodeExecutionState:
        instance = cls(
            id=id_,
            node_execution_id=node_execution_id,
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
            NodeExecutionStateChangedEvent.now(
                node_execution_id=self._node_execution_id,
                node_execution_state_id=self.id,
                now=self._created_at,
            )
        )

    def get(self, key: str) -> object | None:
        return json.loads(self._state_data.value.value).get(key)  # type: ignore[no-any-return]

    def _delete(self, key: str) -> None:
        if json.loads(self._state_data.value.value).get(key) is not None:
            new_data = json.loads(self._state_data.value.value)
            new_data.pop(key, None)
            self._state_data = StateData(JsonStr(json.dumps(new_data)))
            self.append_event(
                NodeExecutionStateChangedEvent.now(
                    node_execution_id=self._node_execution_id,
                    node_execution_state_id=self.id,
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
            self.delete(key)

    def snapshot(self) -> StateData:
        return self._state_data
