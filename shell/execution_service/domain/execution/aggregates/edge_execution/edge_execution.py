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
from shell.execution_service.domain.execution.aggregates.edge_execution.events.edge_execution_created_event import (
    EdgeExecutionCreatedEvent,
)
from shell.execution_service.domain.execution.aggregates.edge_execution.events.edge_execution_deleted_event import (
    EdgeExecutionDeletedEvent,
)
from shell.execution_service.domain.execution.aggregates.edge_execution.events.edge_execution_updated_event import (
    EdgeExecutionUpdatedEvent,
)
from shell.platform.domain.value_objects.deleted_at import NONE_DELETED_AT, DeletedAt
from shell.platform.domain.value_objects.updated_at import NONE_UPDATED_AT, UpdatedAt


class EdgeExecution(AggregateRoot[EdgeExecutionId]):
    __slots__ = (
        "_created_at",
        "_updated_at",
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
        updated_at: UpdatedAt = NONE_UPDATED_AT,
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
        self._updated_at = updated_at
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
        updated_at: UpdatedAt = NONE_UPDATED_AT,
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
            updated_at=updated_at,
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
        now: UpdatedAt,
    ) -> None:
        if self._deleted_at.value is not None:
            raise DomainError("Cannot change target on a deleted edge")
        self._target_node_execution_id = target_node_execution_id
        self._updated_at = now
        self.append_event(
            EdgeExecutionUpdatedEvent.now(
                edge_execution_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def _update(self, now: CreatedAt) -> None:
        self._updated_at = UpdatedAt.from_datetime(now.value)
        self.append_event(
            EdgeExecutionUpdatedEvent.now(
                edge_execution_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._updated_at = UpdatedAt.from_datetime(now.value)
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
        self._updated_at = UpdatedAt.from_datetime(now.value)
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
