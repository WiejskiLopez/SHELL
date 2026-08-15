from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.execution_service.domain.execution.aggregates.edge_link_execution.value_objects.edge_link_execution_id import (
    EdgeLinkExecutionId,
)
from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.exceptions.domain_error import DomainError
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import NONE_DELETED_AT, DeletedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt

if TYPE_CHECKING:
    from shell.execution_service.domain.execution.aggregates.edge_execution.value_objects.edge_execution_id import (
        EdgeExecutionId,
    )
    from shell.execution_service.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )
from shell.execution_service.domain.execution.aggregates.edge_link_execution.events.edge_link_execution_created_event import (
    EdgeLinkExecutionCreatedEvent,
)
from shell.execution_service.domain.execution.aggregates.edge_link_execution.events.edge_link_execution_deleted_event import (
    EdgeLinkExecutionDeletedEvent,
)
from shell.execution_service.domain.execution.aggregates.edge_link_execution.events.edge_link_execution_updated_event import (
    EdgeLinkExecutionUpdatedEvent,
)
from shell.platform.domain.value_objects.updated_at import NONE_UPDATED_AT, UpdatedAt


class EdgeLinkExecution(AggregateRoot[EdgeLinkExecutionId]):
    __slots__ = (
        "_created_at",
        "_updated_at",
        "_deleted_at",
        "_node_execution_id",
        "_edge_execution_id",
    )

    def __init__(
        self,
        *,
        id_: EdgeLinkExecutionId,
        created_at: CreatedAt,
        updated_at: UpdatedAt = NONE_UPDATED_AT,
        deleted_at: DeletedAt = NONE_DELETED_AT,
        node_execution_id: NodeExecutionId,
        edge_execution_id: EdgeExecutionId,
    ) -> None:
        super().__init__(id_)
        self._node_execution_id = node_execution_id
        self._edge_execution_id = edge_execution_id
        self._created_at = created_at
        self._updated_at = updated_at
        self._deleted_at = deleted_at

    @classmethod
    def new(
        cls,
        *,
        id_: EdgeLinkExecutionId,
        node_execution_id: NodeExecutionId,
        edge_execution_id: EdgeExecutionId,
        now: CreatedAt,
    ) -> EdgeLinkExecution:
        instance = cls(
            id_=id_,
            node_execution_id=node_execution_id,
            edge_execution_id=edge_execution_id,
            created_at=CreatedAt.from_datetime(now.value),
        )
        instance.append_event(
            EdgeLinkExecutionCreatedEvent.now(
                edge_link_execution_id=id_,
                node_execution_id=node_execution_id,
                edge_execution_id=edge_execution_id,
                now=OccurredAt.from_datetime(now.value),
            )
        )
        return instance

    def mark_deleted(self, now: DeletedAt) -> None:
        if self._deleted_at.value is not None:
            raise DomainError("Edge link already deleted")
        self._deleted_at = now

        self.append_event(
            EdgeLinkExecutionDeletedEvent.now(
                edge_link_execution_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def update(self, now: UpdatedAt) -> None:
        if self._deleted_at.value is not None:
            raise DomainError("Cannot update a deleted edge link")
        self._updated_at = now
        self.append_event(
            EdgeLinkExecutionUpdatedEvent.now(
                edge_link_execution_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._updated_at = UpdatedAt.from_datetime(now.value)
        self.append_event(
            EdgeLinkExecutionDeletedEvent.now(
                edge_link_execution_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def _update(self, now: UpdatedAt) -> None:
        self._updated_at = now
        self.append_event(
            EdgeLinkExecutionUpdatedEvent.now(
                edge_link_execution_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    @property
    def node_execution_id(self) -> NodeExecutionId:
        return self._node_execution_id

    @property
    def edge_execution_id(self) -> EdgeExecutionId:
        return self._edge_execution_id

    @classmethod
    def restore(
        cls,
        *,
        id_: EdgeLinkExecutionId,
        created_at: CreatedAt,
        updated_at: UpdatedAt = NONE_UPDATED_AT,
        deleted_at: DeletedAt = NONE_DELETED_AT,
        node_execution_id: NodeExecutionId,
        edge_execution_id: EdgeExecutionId,
    ) -> Self:
        return cls(
            id_=id_,
            node_execution_id=node_execution_id,
            edge_execution_id=edge_execution_id,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
        )

    @classmethod
    def _new(
        cls,
        *,
        id_: EdgeLinkExecutionId,
        now: OccurredAt,
        node_execution_id: NodeExecutionId,
        edge_execution_id: EdgeExecutionId,
    ) -> EdgeLinkExecution:
        instance = cls(
            id_=id_,
            node_execution_id=node_execution_id,
            edge_execution_id=edge_execution_id,
            created_at=CreatedAt.from_datetime(now.value),
        )
        instance.append_event(
            EdgeLinkExecutionCreatedEvent.now(
                edge_link_execution_id=id_,
                node_execution_id=node_execution_id,
                edge_execution_id=edge_execution_id,
                now=OccurredAt.from_datetime(now.value),
            )
        )
        return instance
