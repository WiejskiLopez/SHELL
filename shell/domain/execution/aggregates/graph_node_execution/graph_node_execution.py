from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
    GraphNodeExecutionId,
)
from shell.domain.execution.value_objects.error_description import ErrorDescription
from shell.domain.execution.value_objects.graph_node_execution_status import (
    GraphNodeExecutionStatus,
)
from shell.domain.execution.value_objects.node_order import NodeOrder
from shell.domain.execution.value_objects.node_role import NodeRole
from shell.domain.execution.value_objects.node_type import NodeType
from shell.domain.execution.value_objects.remaining_retries import RemainingRetries
from shell.domain.execution.value_objects.retry_delay_seconds import RetryDelaySeconds
from shell.domain.execution.value_objects.timeout_seconds import TimeoutSeconds
from shell.domain.platform.base.aggregate_root import AggregateRoot
from shell.domain.platform.value_objects.mode import Mode

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )


class GraphNodeExecution(AggregateRoot[GraphNodeExecutionId]):
    __slots__ = (
        "_graph_execution_id",
        "_order",
        "_position",
        "_mode",
        "_node_type",
        "_role",
        "_status",
        "_remaining_retries",
        "_retry_delay_seconds",
        "_timeout_seconds",
    )

    def __init__(
        self,
        id: GraphNodeExecutionId,
        graph_execution_id: GraphExecutionId | None = None,
        role: NodeRole = NodeRole.PLANNER,
        order: NodeOrder | None = None,
        position: NodeOrder = NodeOrder(0),
        mode: Mode = Mode.WORKER,
        node_type: NodeType = NodeType(""),
        remaining_retries: RemainingRetries = RemainingRetries(0),
        retry_delay_seconds: RetryDelaySeconds = RetryDelaySeconds(0),
        timeout_seconds: TimeoutSeconds = TimeoutSeconds(0),
        status: GraphNodeExecutionStatus | None = None,
    ) -> None:
        super().__init__(id)
        self._graph_execution_id = graph_execution_id
        self._order = order or NodeOrder(0)
        self._position = position
        self._mode = mode
        self._node_type = node_type
        self._role = role
        self._status = status if status is not None else GraphNodeExecutionStatus.PENDING
        self._remaining_retries = remaining_retries
        self._retry_delay_seconds = retry_delay_seconds
        self._timeout_seconds = timeout_seconds

    @classmethod
    def restore(
        cls,
        id: GraphNodeExecutionId,
        graph_execution_id: GraphExecutionId | None = None,
        role: NodeRole = NodeRole.PLANNER,
        order: NodeOrder | None = None,
        position: NodeOrder = NodeOrder(0),
        mode: Mode = Mode.WORKER,
        node_type: NodeType = NodeType(""),
        remaining_retries: RemainingRetries = RemainingRetries(0),
        retry_delay_seconds: RetryDelaySeconds = RetryDelaySeconds(0),
        timeout_seconds: TimeoutSeconds = TimeoutSeconds(0),
        status: GraphNodeExecutionStatus | None = None,
    ) -> Self:
        return cls(
            id=id,
            graph_execution_id=graph_execution_id,
            role=role,
            order=order,
            position=position,
            mode=mode,
            node_type=node_type,
            remaining_retries=remaining_retries,
            retry_delay_seconds=retry_delay_seconds,
            timeout_seconds=timeout_seconds,
            status=status,
        )

    # --- Factory ---

    @classmethod
    def new(
        cls,
        *,
        id: GraphNodeExecutionId,
        graph_execution_id: GraphExecutionId | None = None,
        parent_graph_execution_id: GraphExecutionId | None = None,
        role: NodeRole = NodeRole.PLANNER,
        order: NodeOrder | None = None,
        position: NodeOrder = NodeOrder(0),
        mode: Mode = Mode.WORKER,
        node_type: NodeType = NodeType(""),
        remaining_retries: RemainingRetries = RemainingRetries(0),
        retry_delay_seconds: RetryDelaySeconds = RetryDelaySeconds(0),
        timeout_seconds: TimeoutSeconds = TimeoutSeconds(0),
        now: datetime,
    ) -> GraphNodeExecution:
        instance = cls(
            id=id,
            graph_execution_id=graph_execution_id,
            role=role,
            order=order,
            position=position,
            mode=mode,
            node_type=node_type,
            remaining_retries=remaining_retries,
            retry_delay_seconds=retry_delay_seconds,
            timeout_seconds=timeout_seconds,
        )
        if parent_graph_execution_id is not None and graph_execution_id is not None:
            from shell.domain.execution.aggregates.graph_node_execution.events.graph_node_execution_initialized_event import (
                GraphNodeExecutionInitializedEvent,
            )

            instance.append_event(
                GraphNodeExecutionInitializedEvent.now(
                    node_id=id,
                    graph_execution_id=graph_execution_id,
                    parent_graph_execution_id=parent_graph_execution_id,
                    now=now,
                )
            )
        return instance

    # --- V3 FSM ---

    def start(self, now: datetime) -> None:
        if self._status != GraphNodeExecutionStatus.PENDING:
            raise InvalidNodeStateError(
                f"Cannot start node in status {self._status}"
            )
        self._status = GraphNodeExecutionStatus.RUNNING
        from shell.domain.execution.aggregates.graph_node_execution.events.graph_node_execution_started_event import (
            GraphNodeExecutionStartedEvent,
        )

        self.append_event(
            GraphNodeExecutionStartedEvent.now(
                node_id=self._id,
                role=self._role,
                now=now,
            )
        )

    def complete(self, result: dict[str, object] | None, now: datetime) -> None:
        if self._status != GraphNodeExecutionStatus.RUNNING:
            raise InvalidNodeStateError(
                f"Cannot complete node in status {self._status}"
            )
        self._status = GraphNodeExecutionStatus.COMPLETED
        from shell.domain.execution.aggregates.graph_node_execution.events.graph_node_execution_completed_event import (
            GraphNodeExecutionCompletedEvent,
        )

        self.append_event(
            GraphNodeExecutionCompletedEvent.now(
                node_id=self._id,
                role=self._role,
                now=now,
                result=result,
            )
        )

    def fail(self, error: ErrorDescription | str, now: datetime) -> None:
        if self._status != GraphNodeExecutionStatus.RUNNING:
            raise InvalidNodeStateError(
                f"Cannot fail node in status {self._status}"
            )
        self._status = GraphNodeExecutionStatus.FAILED
        from shell.domain.execution.aggregates.graph_node_execution.events.graph_node_execution_failed_event import (
            GraphNodeExecutionFailedEvent,
        )

        if isinstance(error, str):
            error = ErrorDescription(error)

        self.append_event(
            GraphNodeExecutionFailedEvent.now(
                node_id=self._id,
                role=self._role,
                now=now,
                error=error,
            )
        )

    def retry(self, now: datetime) -> None:
        if self._status != GraphNodeExecutionStatus.FAILED:
            raise InvalidNodeStateError(
                f"Cannot retry node in status {self._status}"
            )
        if self._remaining_retries <= 0:
            raise InvalidNodeStateError("No remaining retries available")
        self._remaining_retries -= 1
        self._status = GraphNodeExecutionStatus.PENDING
        from shell.domain.execution.aggregates.graph_node_execution.events.graph_node_execution_retried_event import (
            GraphNodeExecutionRetriedEvent,
        )

        self.append_event(
            GraphNodeExecutionRetriedEvent.now(
                node_id=self._id,
                role=self._role,
                remaining_retries=self._remaining_retries,
                retry_delay_seconds=self._retry_delay_seconds,
                now=now,
            )
        )

    def timeout(self, now: datetime) -> None:
        if self._status != GraphNodeExecutionStatus.RUNNING:
            raise InvalidNodeStateError(
                f"Cannot timeout node in status {self._status}"
            )
        self._status = GraphNodeExecutionStatus.TIMED_OUT
        from shell.domain.execution.aggregates.graph_node_execution.events.graph_node_execution_timeout_expired_event import (
            GraphNodeExecutionTimeoutExpiredEvent,
        )

        self.append_event(
            GraphNodeExecutionTimeoutExpiredEvent.now(
                node_id=self._id,
                role=self._role,
                now=now,
            )
        )

    # --- Properties ---

    @property
    def graph_execution_id(self) -> GraphExecutionId | None:
        return self._graph_execution_id

    @property
    def role(self) -> NodeRole:
        return self._role

    @property
    def order(self) -> NodeOrder:
        return self._order

    @property
    def position(self) -> int:
        return self._position

    @property
    def mode(self) -> Mode:
        return self._mode

    @property
    def node_type(self) -> str:
        return self._node_type

    @property
    def status(self) -> GraphNodeExecutionStatus:
        return self._status

    @property
    def remaining_retries(self) -> int:
        return self._remaining_retries

    @property
    def retry_delay_seconds(self) -> int:
        return self._retry_delay_seconds

    @property
    def timeout_seconds(self) -> int:
        return self._timeout_seconds

class InvalidNodeStateError(Exception):
    pass
