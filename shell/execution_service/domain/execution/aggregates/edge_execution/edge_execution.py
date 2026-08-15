from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.execution_service.domain.execution.aggregates.edge_execution.value_objects.edge_execution_id import (
    EdgeExecutionId,
)
from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.exceptions.domain_error import DomainError
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt

if TYPE_CHECKING:
    from shell.execution_service.domain.execution.aggregates.edge_execution.value_objects.edge_definition_id_ref import (
        EdgeDefinitionIdRef,
    )
    from shell.execution_service.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )
from shell.execution_service.domain.execution.aggregates.edge_execution.events.edge_execution_changed_event import (
    EdgeExecutionChangedEvent,
)
from shell.execution_service.domain.execution.aggregates.edge_execution.events.edge_execution_created_event import (
    EdgeExecutionCreatedEvent,
)
from shell.execution_service.domain.execution.aggregates.edge_execution.events.edge_execution_deleted_event import (
    EdgeExecutionDeletedEvent,
)
from shell.platform.domain.value_objects.changed_at import NONE_CHANGED_AT, ChangedAt
from shell.platform.domain.value_objects.deleted_at import NONE_DELETED_AT, DeletedAt


class EdgeExecution(AggregateRoot[EdgeExecutionId]):
    __slots__ = (
        "_created_at",
        "_changed_at",
        "_deleted_at",
        "_edge_definition_id",
        "_source_node_execution_id",
        "_target_node_execution_id",
    )

    def __init__(
        self,
        *,
        id_: EdgeExecutionId,
        created_at: CreatedAt,
        changed_at: ChangedAt = NONE_CHANGED_AT,
        deleted_at: DeletedAt = NONE_DELETED_AT,
        edge_definition_id: EdgeDefinitionIdRef,
        source_node_execution_id: NodeExecutionId,
        target_node_execution_id: NodeExecutionId | None = None,
    ) -> None:
        super().__init__(id_)
        self._edge_definition_id = edge_definition_id
        self._source_node_execution_id = source_node_execution_id
        self._target_node_execution_id = target_node_execution_id
        self._created_at = created_at
        self._changed_at = changed_at
        self._deleted_at = deleted_at

    @classmethod
    def create(
        cls,
        *,
        id_: EdgeExecutionId,
        now: CreatedAt,
        edge_definition_id: EdgeDefinitionIdRef,
        source_node_execution_id: NodeExecutionId,
        target_node_execution_id: NodeExecutionId | None = None,
    ) -> EdgeExecution:
        return cls._new(
            id_=id_,
            edge_definition_id=edge_definition_id,
            source_node_execution_id=source_node_execution_id,
            target_node_execution_id=target_node_execution_id,
            now=OccurredAt.from_datetime(now.value),
        )

    @classmethod
    def restore(
        cls,
        *,
        id_: EdgeExecutionId,
        created_at: CreatedAt,
        changed_at: ChangedAt = NONE_CHANGED_AT,
        deleted_at: DeletedAt = NONE_DELETED_AT,
        edge_definition_id: EdgeDefinitionIdRef,
        source_node_execution_id: NodeExecutionId,
        target_node_execution_id: NodeExecutionId | None = None,
    ) -> Self:
        return cls(
            id_=id_,
            edge_definition_id=edge_definition_id,
            source_node_execution_id=source_node_execution_id,
            target_node_execution_id=target_node_execution_id,
            created_at=created_at,
            changed_at=changed_at,
            deleted_at=deleted_at,
        )

    @classmethod
    def _new(
        cls,
        *,
        id_: EdgeExecutionId,
        now: OccurredAt,
        edge_definition_id: EdgeDefinitionIdRef,
        source_node_execution_id: NodeExecutionId,
        target_node_execution_id: NodeExecutionId | None = None,
    ) -> EdgeExecution:
        instance = cls(
            id_=id_,
            edge_definition_id=edge_definition_id,
            source_node_execution_id=source_node_execution_id,
            target_node_execution_id=target_node_execution_id,
            created_at=CreatedAt.from_datetime(now.value),
        )
        instance.append_event(
            EdgeExecutionCreatedEvent.now(
                edge_execution_id=id_,
                edge_definition_id=edge_definition_id,
                source_node_execution_id=source_node_execution_id,
                target_node_execution_id=target_node_execution_id,
                now=OccurredAt.from_datetime(now.value),
            )
        )
        return instance

    def change_target(
        self,
        target_node_execution_id: NodeExecutionId | None,
        now: OccurredAt,
    ) -> None:
        if self._deleted_at.value is not None:
            raise DomainError("Cannot change target on a deleted edge")
        self._target_node_execution_id = target_node_execution_id
        self._change(now=now)

    def _change(self, now: OccurredAt) -> None:
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            EdgeExecutionChangedEvent.now(
                edge_execution_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            EdgeExecutionDeletedEvent.now(
                edge_execution_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def mark_deleted(self, now: DeletedAt) -> None:
        if self._deleted_at.value is not None:
            raise DomainError("Edge already deleted")
        self._deleted_at = now
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            EdgeExecutionDeletedEvent.now(
                edge_execution_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    @property
    def edge_definition_id(self) -> EdgeDefinitionIdRef:
        return self._edge_definition_id

    @property
    def source_node_execution_id(self) -> NodeExecutionId:
        return self._source_node_execution_id

    @property
    def target_node_execution_id(self) -> NodeExecutionId | None:
        return self._target_node_execution_id
