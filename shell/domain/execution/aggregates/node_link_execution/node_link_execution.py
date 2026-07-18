from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.execution.aggregates.node_link_execution.events.node_link_execution_created_event import (
    NodeLinkExecutionCreatedEvent,
)
from shell.domain.execution.aggregates.node_link_execution.events.node_link_execution_deleted_event import (
    NodeLinkExecutionDeletedEvent,
)
from shell.domain.execution.aggregates.node_link_execution.events.node_link_execution_updated_event import (
    NodeLinkExecutionUpdatedEvent,
)
from shell.domain.execution.aggregates.node_link_execution.value_objects.node_link_execution_id import (
    NodeLinkExecutionId,
)
from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.updated_at import UpdatedAt

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )
    from shell.platform.domain.value_objects.deleted_at import DeletedAt


class NodeLinkExecution(AggregateRoot[NodeLinkExecutionId]):
    __slots__ = (
        "_graph_execution_id",
        "_node_execution_id",
        "_created_at",
        "_updated_at",
        "_deleted_at",
    )

    def __init__(
        self,
        id: NodeLinkExecutionId,
        graph_execution_id: GraphExecutionId,
        node_execution_id: NodeExecutionId,
        created_at: CreatedAt,
        updated_at: UpdatedAt | None = None,
    ) -> None:
        super().__init__(id)
        self._graph_execution_id = graph_execution_id
        self._node_execution_id = node_execution_id
        self._created_at = created_at
        self._updated_at = updated_at

    @classmethod
    def _new(
        cls,
        *,
        id_: NodeLinkExecutionId,
        graph_execution_id: GraphExecutionId,
        node_execution_id: NodeExecutionId,
        now: CreatedAt,
    ) -> NodeLinkExecution:
        instance = cls(
            id=id_,
            graph_execution_id=graph_execution_id,
            node_execution_id=node_execution_id,
            created_at=now,
        )
        instance.append_event(
            NodeLinkExecutionCreatedEvent.now(
                node_link_execution_id=instance.id,
                now=now,
            )
        )
        return instance

    @classmethod
    def create(
        cls,
        *,
        id_: NodeLinkExecutionId,
        graph_execution_id: GraphExecutionId,
        node_execution_id: NodeExecutionId,
        now: CreatedAt,
    ) -> NodeLinkExecution:
        return cls._new(
            id_=id_,
            graph_execution_id=graph_execution_id,
            node_execution_id=node_execution_id,
            now=now,
        )

    @classmethod
    def restore(
        cls,
        id: NodeLinkExecutionId,
        graph_execution_id: GraphExecutionId,
        node_execution_id: NodeExecutionId,
        created_at: CreatedAt,
        updated_at: UpdatedAt | None = None,
    ) -> Self:
        return cls(
            id=id,
            graph_execution_id=graph_execution_id,
            node_execution_id=node_execution_id,
            created_at=created_at,
            updated_at=updated_at,
        )

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._updated_at = UpdatedAt.from_datetime(now.value)
        self.append_event(
            NodeLinkExecutionDeletedEvent.now(
                node_link_execution_id=self._id,
                now=CreatedAt.from_datetime(now.value),
            )
        )

    def _update(self, now: UpdatedAt) -> None:
        self._updated_at = now
        self.append_event(
            NodeLinkExecutionUpdatedEvent.now(
                node_link_execution_id=self._id,
                now=CreatedAt.from_datetime(now.value),
            )
        )

    @property
    def graph_execution_id(self) -> GraphExecutionId:
        return self._graph_execution_id

    @property
    def node_execution_id(self) -> NodeExecutionId:
        return self._node_execution_id

    @property
    def created_at(self) -> CreatedAt | None:
        return self._created_at

    @property
    def updated_at(self) -> UpdatedAt | None:
        return self._updated_at
