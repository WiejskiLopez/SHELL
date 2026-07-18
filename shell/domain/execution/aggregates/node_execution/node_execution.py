from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.execution.aggregates.node_execution.events.node_execution_created_event import (
    NodeExecutionCreatedEvent,
)
from shell.domain.execution.aggregates.node_execution.exceptions.invalid_node_state_error import (
    InvalidNodeStateError,
)
from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
    NodeExecutionId,
)
from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_status import (
    NodeExecutionStatus,
)
from shell.platform.domain.base.aggregate_root import AggregateRoot

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.domain.execution.aggregates.node_execution.value_objects.node_definition_id_ref import (
        NodeDefinitionIdRef,
    )
    from shell.domain.execution.aggregates.node_execution.value_objects.node_order import NodeOrder
    from shell.domain.execution.aggregates.node_execution.value_objects.node_type import NodeType
    from shell.platform.domain.value_objects.created_at import CreatedAt
    from shell.platform.domain.value_objects.error_description import ErrorDescription
    from shell.platform.domain.value_objects.state_data import StateData
    from shell.platform.types import JsonStr


class NodeExecution(AggregateRoot[NodeExecutionId]):
    __slots__ = (
        "_updated_at",
        "_node_definition_id",
        "_order",
        "_node_type",
        "_status",
        "_created_at",
    )

    def __init__(
        self,
        id: NodeExecutionId,
        node_type: NodeType,
        order: NodeOrder,
        status: NodeExecutionStatus,
        created_at: CreatedAt,
        node_definition_id: NodeDefinitionIdRef | None = None,
    ) -> None:
        super().__init__(id)
        self._node_definition_id = node_definition_id
        self._order = order
        self._node_type = node_type
        self._status = status
        self._created_at = created_at

    @classmethod
    def restore(
        cls,
        id: NodeExecutionId,
        node_type: NodeType,
        order: NodeOrder,
        status: NodeExecutionStatus,
        created_at: CreatedAt,
        node_definition_id: NodeDefinitionIdRef | None = None,
    ) -> Self:
        return cls(
            id=id,
            node_type=node_type,
            order=order,
            status=status,
            created_at=created_at,
            node_definition_id=node_definition_id,
        )

    # --- Factory ---

    @classmethod
    def new(
        cls,
        *,
        id: NodeExecutionId,
        node_type: NodeType,
        graph_execution_id: GraphExecutionId | None = None,
        node_definition_id: NodeDefinitionIdRef | None = None,
        order: NodeOrder,
        now: CreatedAt,
    ) -> NodeExecution:
        instance = cls(
            id=id,
            node_type=node_type,
            order=order,
            status=NodeExecutionStatus.PENDING,
            node_definition_id=node_definition_id,
            created_at=now,
        )
        instance.append_event(
            NodeExecutionCreatedEvent.now(
                node_execution_id=id,
                node_definition_id=node_definition_id,
                graph_execution_id=graph_execution_id,
                now=now,
            )
        )
        return instance

    # --- V3 FSM ---

    def start(self) -> None:
        if self._status != NodeExecutionStatus.PENDING:
            raise InvalidNodeStateError(f"Cannot start node in status {self._status}")
        self._status = NodeExecutionStatus.RUNNING

    def complete(self, result: StateData | JsonStr | None) -> None:
        if self._status != NodeExecutionStatus.RUNNING:
            raise InvalidNodeStateError(f"Cannot complete node in status {self._status}")
        self._status = NodeExecutionStatus.COMPLETED

    def fail(self, error: ErrorDescription | str) -> None:
        if self._status != NodeExecutionStatus.RUNNING:
            raise InvalidNodeStateError(f"Cannot fail node in status {self._status}")
        self._status = NodeExecutionStatus.FAILED

    def retry(self) -> None:
        if self._status != NodeExecutionStatus.FAILED:
            raise InvalidNodeStateError(f"Cannot retry node in status {self._status}")
        self._status = NodeExecutionStatus.PENDING

    def timeout(self) -> None:
        if self._status != NodeExecutionStatus.RUNNING:
            raise InvalidNodeStateError(f"Cannot timeout node in status {self._status}")
        self._status = NodeExecutionStatus.TIMED_OUT

    # --- Properties ---


    @classmethod
    def _update(cls) -> None:
        raise NotImplementedError("_update() not yet implemented")


    @classmethod
    def _new(cls) -> NodeExecution:
        raise NotImplementedError("_new() not yet implemented")

    def _delete(self) -> None:
        raise NotImplementedError("_delete() not yet implemented")

    @property
    def node_definition_id(self) -> NodeDefinitionIdRef | None:
        return self._node_definition_id

    @property
    def order(self) -> NodeOrder:
        return self._order

    @property
    def node_type(self) -> NodeType:
        return self._node_type

    @property
    def status(self) -> NodeExecutionStatus:
        return self._status

    @property
    def created_at(self) -> CreatedAt:
        return self._created_at
