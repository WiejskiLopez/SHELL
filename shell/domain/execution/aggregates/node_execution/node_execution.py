from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.execution.aggregates.node_execution.exceptions.invalid_node_state_error import (
    InvalidNodeStateError,
)
from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
    NodeExecutionId,
)
from shell.domain.execution.value_objects.error_description import ErrorDescription
from shell.domain.execution.value_objects.node_definition_id import NodeDefinitionId
from shell.domain.execution.value_objects.node_execution_status import (
    NodeExecutionStatus,
)
from shell.domain.execution.value_objects.node_order import NodeOrder
from shell.domain.platform.base.aggregate_root import AggregateRoot
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.state_data import StateData

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.domain.execution.value_objects.node_role import NodeRole
    from shell.domain.execution.value_objects.node_type import NodeType
    from shell.domain.platform.value_objects.mode import Mode


from shell.domain.execution.aggregates.node_execution.events.node_execution_timeout_expired_event import (
            NodeExecutionTimeoutExpiredEvent,
        )
from shell.domain.execution.aggregates.node_execution.events.node_execution_retried_event import (
            NodeExecutionRetriedEvent,
        )
from shell.domain.execution.aggregates.node_execution.events.node_execution_failed_event import (
            NodeExecutionFailedEvent,
        )
from shell.domain.execution.aggregates.node_execution.events.node_execution_completed_event import (
            NodeExecutionCompletedEvent,
        )
from shell.domain.execution.aggregates.node_execution.events.node_execution_started_event import (
            NodeExecutionStartedEvent,
        )
from shell.domain.execution.aggregates.node_execution.events.node_execution_initialized_event import (
                NodeExecutionInitializedEvent,
            )
class NodeExecution(AggregateRoot[NodeExecutionId]):
    __slots__ = (
        "_node_definition_id",
        "_order",
        "_position",
        "_mode",
        "_node_type",
        "_role",
        "_status",
    )

    def __init__(
        self,
        id: NodeExecutionId,
        role: NodeRole,
        position: NodeOrder,
        mode: Mode,
        node_type: NodeType,
        node_definition_id: NodeDefinitionId | None = None,
        order: NodeOrder | None = None,
        status: NodeExecutionStatus | None = None,
    ) -> None:
        super().__init__(id)
        self._node_definition_id = node_definition_id
        self._order = order or NodeOrder(0)
        self._position = position
        self._mode = mode
        self._node_type = node_type
        self._role = role
        self._status = status if status is not None else NodeExecutionStatus.PENDING

    @classmethod
    def restore(
        cls,
        id: NodeExecutionId,
        role: NodeRole,
        position: NodeOrder,
        mode: Mode,
        node_type: NodeType,
        node_definition_id: NodeDefinitionId | None = None,
        order: NodeOrder | None = None,
        status: NodeExecutionStatus | None = None,
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
        order: NodeOrder | None = None,
        now: datetime,
    ) -> NodeExecution:
        instance = cls(
            id=id,
            node_definition_id=node_definition_id,
            role=role,
            order=order,
            position=position,
            mode=mode,
            node_type=node_type,
        )
        if graph_execution_id is not None:
            instance.append_event(
                NodeExecutionInitializedEvent.now(
                    node_id=id,
                    graph_execution_id=graph_execution_id,
                    node_definition_id=node_definition_id or NodeDefinitionId(""),
                    now=CreatedAt.from_datetime(now),
                )
            )
        return instance

    # --- V3 FSM ---

    def start(self, now: datetime) -> None:
        if self._status != NodeExecutionStatus.PENDING:
            raise InvalidNodeStateError(f"Cannot start node in status {self._status}")
        self._status = NodeExecutionStatus.RUNNING
        self.append_event(
            NodeExecutionStartedEvent.now(
                node_id=self._id,
                role=self._role,
                now=CreatedAt.from_datetime(now),
            )
        )

    def complete(self, result: StateData | dict[str, object] | None, now: datetime) -> None:
        if self._status != NodeExecutionStatus.RUNNING:
            raise InvalidNodeStateError(f"Cannot complete node in status {self._status}")
        self._status = NodeExecutionStatus.COMPLETED
        actual_result = StateData(result) if isinstance(result, dict) else result
        self.append_event(
            NodeExecutionCompletedEvent.now(
                node_id=self._id,
                role=self._role,
                now=CreatedAt.from_datetime(now),
                result=actual_result,
            )
        )

    def fail(self, error: ErrorDescription | str, now: datetime) -> None:
        if self._status != NodeExecutionStatus.RUNNING:
            raise InvalidNodeStateError(f"Cannot fail node in status {self._status}")
        self._status = NodeExecutionStatus.FAILED
        if isinstance(error, str):
            error = ErrorDescription(error)

        self.append_event(
            NodeExecutionFailedEvent.now(
                node_id=self._id,
                role=self._role,
                now=CreatedAt.from_datetime(now),
                error=error,
            )
        )

    def retry(self, now: datetime) -> None:
        if self._status != NodeExecutionStatus.FAILED:
            raise InvalidNodeStateError(f"Cannot retry node in status {self._status}")
        self._status = NodeExecutionStatus.PENDING
        self.append_event(
            NodeExecutionRetriedEvent.now(
                node_id=self._id,
                role=self._role,
                now=CreatedAt.from_datetime(now),
            )
        )

    def timeout(self, now: datetime) -> None:
        if self._status != NodeExecutionStatus.RUNNING:
            raise InvalidNodeStateError(f"Cannot timeout node in status {self._status}")
        self._status = NodeExecutionStatus.TIMED_OUT
        self.append_event(
            NodeExecutionTimeoutExpiredEvent.now(
                node_id=self._id,
                role=self._role,
                now=CreatedAt.from_datetime(now),
            )
        )

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

