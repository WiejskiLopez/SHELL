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
    from shell.domain.execution.aggregates.node_execution.value_objects.node_definition_id import (
        NodeDefinitionId,
    )
    from shell.domain.execution.aggregates.node_execution.value_objects.node_order import NodeOrder
    from shell.domain.execution.aggregates.node_execution.value_objects.node_role import NodeRole
    from shell.domain.execution.aggregates.node_execution.value_objects.node_type import NodeType
    from shell.platform.domain.value_objects.created_at import CreatedAt
    from shell.platform.domain.value_objects.error_description import ErrorDescription
    from shell.platform.domain.value_objects.mode import Mode
    from shell.platform.domain.value_objects.state_data import StateData
    from shell.platform.types import JsonStr


class NodeExecution(AggregateRoot[NodeExecutionId]):
    __slots__ = (
        "_node_definition_id",
        "_order",
        "_position",
        "_mode",
        "_node_type",
        "_role",
        "_status",
        "_created_at",
    )

    def __init__(
        self,
        id: NodeExecutionId,
        role: NodeRole,
        position: NodeOrder,
        mode: Mode,
        node_type: NodeType,
        order: NodeOrder,
        status: NodeExecutionStatus,
        node_definition_id: NodeDefinitionId | None = None,
        created_at: CreatedAt | None = None,
    ) -> None:
        super().__init__(id)
        self._node_definition_id = node_definition_id
        self._order = order
        self._position = position
        self._mode = mode
        self._node_type = node_type
        self._role = role
        self._status = status
        self._created_at = created_at

    @classmethod
    def restore(
        cls,
        id: NodeExecutionId,
        role: NodeRole,
        position: NodeOrder,
        mode: Mode,
        node_type: NodeType,
        order: NodeOrder,
        status: NodeExecutionStatus,
        node_definition_id: NodeDefinitionId | None = None,
        created_at: CreatedAt | None = None,
    ) -> Self:
        return cls(
            id=id,
            node_definition_id=node_definition_id,
            role=role,
            order=order,
            position=position,
            mode=mode,
            node_type=node_type,
            status=status,
            created_at=created_at,
        )

    # --- Factory ---

    @classmethod
    def new(
        cls,
        *,
        id: NodeExecutionId,
        role: NodeRole,
        position: NodeOrder,
        mode: Mode,
        node_type: NodeType,
        graph_execution_id: GraphExecutionId | None = None,
        node_definition_id: NodeDefinitionId | None = None,
        order: NodeOrder,
        now: CreatedAt,
    ) -> NodeExecution:
        instance = cls(
            id=id,
            node_definition_id=node_definition_id,
            role=role,
            order=order,
            position=position,
            mode=mode,
            node_type=node_type,
            status=NodeExecutionStatus.PENDING,
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

    @property
    def node_definition_id(self) -> NodeDefinitionId | None:
        return self._node_definition_id

    @property
    def role(self) -> NodeRole:
        return self._role

    @property
    def order(self) -> NodeOrder:
        return self._order

    @property
    def position(self) -> NodeOrder:
        return self._position

    @property
    def mode(self) -> Mode:
        return self._mode

    @property
    def node_type(self) -> NodeType:
        return self._node_type

    @property
    def status(self) -> NodeExecutionStatus:
        return self._status
