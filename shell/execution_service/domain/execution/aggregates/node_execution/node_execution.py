from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.execution_service.domain.execution.aggregates.node_execution.events.node_execution_changed_event import (
    NodeExecutionChangedEvent,
)
from shell.execution_service.domain.execution.aggregates.node_execution.events.node_execution_created_event import (
    NodeExecutionCreatedEvent,
)
from shell.execution_service.domain.execution.aggregates.node_execution.events.node_execution_deleted_event import (
    NodeExecutionDeletedEvent,
)
from shell.execution_service.domain.execution.aggregates.node_execution.exceptions.invalid_node_state_error import (
    InvalidNodeStateError,
)
from shell.execution_service.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
    NodeExecutionId,
)
from shell.execution_service.domain.execution.aggregates.node_execution.value_objects.node_execution_status import (
    NodeExecutionStatus,
)
from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.exceptions import DomainError
from shell.platform.domain.value_objects.changed_at import NONE_CHANGED_AT, ChangedAt
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import NONE_DELETED_AT, DeletedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt

if TYPE_CHECKING:
    from shell.execution_service.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.execution_service.domain.execution.aggregates.node_execution.value_objects.node_definition_id_ref import (
        NodeDefinitionIdRef,
    )
    from shell.execution_service.domain.execution.aggregates.node_execution.value_objects.node_order import (
        NodeOrder,
    )
    from shell.execution_service.domain.execution.aggregates.node_execution.value_objects.node_type import (
        NodeType,
    )


class NodeExecution(AggregateRoot[NodeExecutionId]):
    __slots__ = (
        "_created_at",
        "_changed_at",
        "_deleted_at",
        "_node_definition_id",
        "_order",
        "_node_type",
        "_status",
    )

    def __init__(
        self,
        id: NodeExecutionId,
        *,
        created_at: CreatedAt,
        changed_at: ChangedAt = NONE_CHANGED_AT,
        deleted_at: DeletedAt = NONE_DELETED_AT,
        node_type: NodeType,
        order: NodeOrder,
        status: NodeExecutionStatus,
        node_definition_id: NodeDefinitionIdRef | None = None,
    ) -> None:
        super().__init__(id)
        self._node_definition_id = node_definition_id
        self._order = order
        self._node_type = node_type
        self._status = status
        self._created_at = created_at
        self._changed_at = changed_at
        self._deleted_at = deleted_at

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
        return cls._new(
            id=id,
            node_type=node_type,
            graph_execution_id=graph_execution_id,
            node_definition_id=node_definition_id,
            order=order,
            now=OccurredAt.from_datetime(now.value),
        )

    # --- V3 FSM ---

    def start(self) -> None:
        if self._deleted_at is not None and self._deleted_at.value is not None:
            raise InvalidNodeStateError(f"Cannot start deleted node in status {self._status}")
        if self._status != NodeExecutionStatus.PENDING:
            raise InvalidNodeStateError(f"Cannot start node in status {self._status}")
        self._status = NodeExecutionStatus.RUNNING

    def complete(self) -> None:
        if self._deleted_at is not None and self._deleted_at.value is not None:
            raise InvalidNodeStateError(f"Cannot complete deleted node in status {self._status}")
        if self._status != NodeExecutionStatus.RUNNING:
            raise InvalidNodeStateError(f"Cannot complete node in status {self._status}")
        self._status = NodeExecutionStatus.COMPLETED

    def fail(self) -> None:
        if self._deleted_at is not None and self._deleted_at.value is not None:
            raise InvalidNodeStateError(f"Cannot fail deleted node in status {self._status}")
        if self._status != NodeExecutionStatus.RUNNING:
            raise InvalidNodeStateError(f"Cannot fail node in status {self._status}")
        self._status = NodeExecutionStatus.FAILED

    def retry(self) -> None:
        if self._deleted_at is not None and self._deleted_at.value is not None:
            raise InvalidNodeStateError(f"Cannot retry deleted node in status {self._status}")
        if self._status != NodeExecutionStatus.FAILED:
            raise InvalidNodeStateError(f"Cannot retry node in status {self._status}")
        self._status = NodeExecutionStatus.PENDING

    def timeout(self) -> None:
        if self._deleted_at is not None and self._deleted_at.value is not None:
            raise InvalidNodeStateError(f"Cannot timeout deleted node in status {self._status}")
        if self._status != NodeExecutionStatus.RUNNING:
            raise InvalidNodeStateError(f"Cannot timeout node in status {self._status}")
        self._status = NodeExecutionStatus.TIMED_OUT

    def mark_deleted(self, now: DeletedAt) -> None:
        if self._deleted_at is not None and self._deleted_at.value is not None:
            raise DomainError("Node execution already deleted")
        self._delete(now)

    # --- Properties ---

    def _change(self, now: OccurredAt) -> None:
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            NodeExecutionChangedEvent.now(
                node_execution_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            NodeExecutionDeletedEvent.now(
                node_execution_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

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

    @property
    def changed_at(self) -> ChangedAt:
        return self._changed_at

    @classmethod
    def restore(
        cls,
        id: NodeExecutionId,
        *,
        created_at: CreatedAt,
        changed_at: ChangedAt = NONE_CHANGED_AT,
        deleted_at: DeletedAt = NONE_DELETED_AT,
        node_type: NodeType,
        order: NodeOrder,
        status: NodeExecutionStatus,
        node_definition_id: NodeDefinitionIdRef | None = None,
    ) -> Self:
        return cls(
            id=id,
            node_type=node_type,
            order=order,
            status=status,
            created_at=created_at,
            changed_at=changed_at,
            deleted_at=deleted_at,
            node_definition_id=node_definition_id,
        )

    # --- Factory ---

    @classmethod
    def _new(
        cls,
        *,
        id: NodeExecutionId,
        now: OccurredAt,
        node_type: NodeType,
        graph_execution_id: GraphExecutionId | None = None,
        node_definition_id: NodeDefinitionIdRef | None = None,
        order: NodeOrder,
    ) -> NodeExecution:
        instance = cls(
            id=id,
            node_type=node_type,
            order=order,
            status=NodeExecutionStatus.PENDING,
            node_definition_id=node_definition_id,
            created_at=CreatedAt.from_datetime(now.value),
        )
        instance.append_event(
            NodeExecutionCreatedEvent.now(
                node_execution_id=id,
                node_definition_id=node_definition_id,
                graph_execution_id=graph_execution_id,
                now=OccurredAt.from_datetime(now.value),
            )
        )
        return instance
