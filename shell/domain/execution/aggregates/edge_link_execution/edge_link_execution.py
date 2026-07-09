from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.execution.aggregates.edge_link_execution.value_objects.edge_link_execution_id import (
    EdgeLinkExecutionId,
)
from shell.domain.platform.base.aggregate_root import AggregateRoot
from shell.domain.platform.value_objects.created_at import CreatedAt

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.execution.aggregates.edge_execution.value_objects.edge_execution_id import (
        EdgeExecutionId,
    )
    from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )
from shell.domain.execution.aggregates.edge_link_execution.events.edge_link_execution_created_event import (
    EdgeLinkExecutionCreatedEvent,
)
from shell.domain.execution.aggregates.edge_link_execution.events.edge_link_execution_deleted_event import (
    EdgeLinkExecutionDeletedEvent,
)
from shell.domain.platform.value_objects.deleted_at import DeletedAt
from shell.domain.platform.value_objects.updated_at import UpdatedAt


class EdgeLinkExecution(AggregateRoot[EdgeLinkExecutionId]):
    __slots__ = (
        "_node_execution_id",
        "_edge_execution_id",
        "_created_at",
        "_updated_at",
        "_deleted_at",
    )

    def __init__(
        self,
        id_: EdgeLinkExecutionId,
        node_execution_id: NodeExecutionId,
        edge_execution_id: EdgeExecutionId,
        created_at: CreatedAt | None = None,
        updated_at: UpdatedAt | None = None,
        deleted_at: DeletedAt | None = None,
    ) -> None:
        super().__init__(id_)
        self._node_execution_id = node_execution_id
        self._edge_execution_id = edge_execution_id
        self._created_at = created_at
        self._updated_at = updated_at
        self._deleted_at = deleted_at

    @classmethod
    def restore(
        cls,
        id_: EdgeLinkExecutionId,
        node_execution_id: NodeExecutionId,
        edge_execution_id: EdgeExecutionId,
        created_at: CreatedAt | None = None,
        updated_at: UpdatedAt | None = None,
        deleted_at: DeletedAt | None = None,
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
    def new(
        cls,
        *,
        id_: EdgeLinkExecutionId,
        node_execution_id: NodeExecutionId,
        edge_execution_id: EdgeExecutionId,
        now: datetime,
    ) -> EdgeLinkExecution:
        instance = cls(
            id_=id_,
            node_execution_id=node_execution_id,
            edge_execution_id=edge_execution_id,
        )
        instance.append_event(
            EdgeLinkExecutionCreatedEvent.now(
                edge_link_execution_id=id_,
                node_execution_id=node_execution_id,
                edge_execution_id=edge_execution_id,
                now=CreatedAt.from_datetime(now),
            )
        )
        return instance

    def mark_deleted(self, now: datetime) -> None:
        self._deleted_at = DeletedAt.from_datetime(now)
        self._updated_at = UpdatedAt.from_datetime(now)
        self.append_event(
            EdgeLinkExecutionDeletedEvent.now(
                edge_link_execution_id=self._id,
                now=CreatedAt.from_datetime(now),
            )
        )

    def update(self, now: datetime) -> None:
        self._updated_at = UpdatedAt.from_datetime(now)

    @property
    def node_execution_id(self) -> NodeExecutionId:
        return self._node_execution_id

    @property
    def edge_execution_id(self) -> EdgeExecutionId:
        return self._edge_execution_id
