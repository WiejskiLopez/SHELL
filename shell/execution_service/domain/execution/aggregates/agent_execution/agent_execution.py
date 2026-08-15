from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.execution_service.domain.execution.aggregates.agent_execution.events.agent_execution_changed_event import (
    AgentExecutionChangedEvent,
)
from shell.execution_service.domain.execution.aggregates.agent_execution.events.agent_execution_created_event import (
    AgentExecutionCreatedEvent,
)
from shell.execution_service.domain.execution.aggregates.agent_execution.events.agent_execution_deleted_event import (
    AgentExecutionDeletedEvent,
)
from shell.execution_service.domain.execution.aggregates.agent_execution.value_objects.agent_execution_id import (
    AgentExecutionId,
)
from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.value_objects.changed_at import NONE_CHANGED_AT, ChangedAt
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt

if TYPE_CHECKING:
    from shell.execution_service.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )
    from shell.platform.domain.value_objects.deleted_at import DeletedAt


class AgentExecution(AggregateRoot[AgentExecutionId]):
    __slots__ = (
        "_created_at",
        "_changed_at",
        "_deleted_at",
        "_node_execution_id",
    )

    _node_execution_id: NodeExecutionId
    _created_at: CreatedAt
    _changed_at: ChangedAt

    def __init__(
        self,
        *,
        id_: AgentExecutionId,
        created_at: CreatedAt,
        changed_at: ChangedAt = NONE_CHANGED_AT,
        node_execution_id: NodeExecutionId,
    ) -> None:
        super().__init__(id_)
        self._node_execution_id = node_execution_id
        self._created_at = created_at
        self._changed_at = changed_at

    @classmethod
    def _new(
        cls,
        *,
        id_: AgentExecutionId,
        now: OccurredAt,
        node_execution_id: NodeExecutionId,
    ) -> AgentExecution:
        instance = cls(
            id_=id_,
            node_execution_id=node_execution_id,
            created_at=CreatedAt.from_datetime(now.value),
        )
        instance.append_event(
            AgentExecutionCreatedEvent.now(
                agent_execution_id=instance.id,
                now=OccurredAt.from_datetime(now.value),
            )
        )
        return instance

    @classmethod
    def create(
        cls,
        *,
        id_: AgentExecutionId,
        now: CreatedAt,
        node_execution_id: NodeExecutionId,
    ) -> AgentExecution:
        return cls._new(
            id_=id_, node_execution_id=node_execution_id, now=OccurredAt.from_datetime(now.value)
        )

    @classmethod
    def restore(
        cls,
        *,
        id_: AgentExecutionId,
        created_at: CreatedAt,
        changed_at: ChangedAt = NONE_CHANGED_AT,
        node_execution_id: NodeExecutionId,
    ) -> Self:
        return cls(
            id_=id_,
            node_execution_id=node_execution_id,
            created_at=created_at,
            changed_at=changed_at,
        )

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            AgentExecutionDeletedEvent.now(
                agent_execution_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def _change(self, now: OccurredAt) -> None:
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            AgentExecutionChangedEvent.now(
                agent_execution_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    @property
    def node_execution_id(self) -> NodeExecutionId:
        return self._node_execution_id

    @property
    def created_at(self) -> CreatedAt:
        return self._created_at

    @property
    def changed_at(self) -> ChangedAt:
        return self._changed_at
