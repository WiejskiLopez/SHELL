from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.execution.aggregates.edge_execution.value_objects.edge_execution_id import (
    EdgeExecutionId,
)
from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.value_objects.created_at import CreatedAt

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.edge_execution.value_objects.edge_definition_id import (
        EdgeDefinitionId,
    )
    from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )
from shell.domain.execution.aggregates.edge_execution.events.edge_execution_created_event import (
    EdgeExecutionCreatedEvent,
)
from shell.domain.execution.aggregates.edge_execution.events.edge_execution_deleted_event import (
    EdgeExecutionDeletedEvent,
)
from shell.domain.execution.aggregates.edge_execution.events.edge_execution_updated_event import (
    EdgeExecutionUpdatedEvent,
)
from shell.platform.domain.value_objects.updated_at import UpdatedAt

if TYPE_CHECKING:
    from shell.platform.domain.value_objects.deleted_at import DeletedAt


class EdgeExecution(AggregateRoot[EdgeExecutionId]):
    __slots__ = (
        "_edge_definition_id",
        "_source_node_execution_id",
        "_target_node_execution_id",
        "_created_at",
        "_updated_at",
        "_deleted_at",
    )

    def __init__(
        self,
        id_: EdgeExecutionId,
        edge_definition_id: EdgeDefinitionId,
        source_node_execution_id: NodeExecutionId,
        target_node_execution_id: NodeExecutionId | None = None,
        created_at: CreatedAt | None = None,
        updated_at: UpdatedAt | None = None,
        deleted_at: DeletedAt | None = None,
    ) -> None:
        super().__init__(id_)
        self._edge_definition_id = edge_definition_id
        self._source_node_execution_id = source_node_execution_id
        self._target_node_execution_id = target_node_execution_id
        self._created_at = created_at
        self._updated_at = updated_at
        self._deleted_at = deleted_at

    @classmethod
    def restore(
        cls,
        id_: EdgeExecutionId,
        edge_definition_id: EdgeDefinitionId,
        source_node_execution_id: NodeExecutionId,
        target_node_execution_id: NodeExecutionId | None = None,
        created_at: CreatedAt | None = None,
        updated_at: UpdatedAt | None = None,
        deleted_at: DeletedAt | None = None,
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
    def new(
        cls,
        *,
        id_: EdgeExecutionId,
        edge_definition_id: EdgeDefinitionId,
        source_node_execution_id: NodeExecutionId,
        target_node_execution_id: NodeExecutionId | None = None,
        now: CreatedAt,
    ) -> EdgeExecution:
        instance = cls(
            id_=id_,
            edge_definition_id=edge_definition_id,
            source_node_execution_id=source_node_execution_id,
            target_node_execution_id=target_node_execution_id,
        )
        instance.append_event(
            EdgeExecutionCreatedEvent.now(
                edge_execution_id=id_,
                edge_definition_id=edge_definition_id,
                source_node_execution_id=source_node_execution_id,
                target_node_execution_id=target_node_execution_id,
                now=now,
            )
        )
        return instance

    def change_target(
        self,
        target_node_execution_id: NodeExecutionId | None,
        now: UpdatedAt,
    ) -> None:
        if self._deleted_at is not None:
            raise ValueError("Cannot change target on a deleted edge")
        self._target_node_execution_id = target_node_execution_id
        self._updated_at = now
        self.append_event(
            EdgeExecutionUpdatedEvent.now(
                edge_execution_id=self._id,
                now=CreatedAt.from_datetime(now.value),
            )
        )

    def mark_deleted(self, now: DeletedAt) -> None:
        if self._deleted_at is not None:
            raise ValueError("Edge already deleted")
        self._deleted_at = now
        self._updated_at = UpdatedAt.from_datetime(now.value)
        self.append_event(
            EdgeExecutionDeletedEvent.now(
                edge_execution_id=self._id,
                now=CreatedAt.from_datetime(now.value),
            )
        )

    @property
    def edge_definition_id(self) -> EdgeDefinitionId:
        return self._edge_definition_id

    @property
    def source_node_execution_id(self) -> NodeExecutionId:
        return self._source_node_execution_id

    @property
    def target_node_execution_id(self) -> NodeExecutionId | None:
        return self._target_node_execution_id
