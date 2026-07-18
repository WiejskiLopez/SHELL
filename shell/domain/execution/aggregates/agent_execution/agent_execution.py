from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.execution.aggregates.agent_execution.events.agent_execution_created_event import (
    AgentExecutionCreatedEvent,
)
from shell.domain.execution.aggregates.agent_execution.events.agent_execution_deleted_event import (
    AgentExecutionDeletedEvent,
)
from shell.domain.execution.aggregates.agent_execution.events.agent_execution_updated_event import (
    AgentExecutionUpdatedEvent,
)
from shell.domain.execution.aggregates.agent_execution.value_objects.agent_execution_id import (
    AgentExecutionId,
)
from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.updated_at import UpdatedAt

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )
    from shell.platform.domain.value_objects.deleted_at import DeletedAt

class AgentExecution(AggregateRoot[AgentExecutionId]):
    __slots__ = (
        "_node_execution_id",
        "_created_at",
        "_updated_at",
    )

    _node_execution_id: NodeExecutionId
    _created_at: CreatedAt
    _updated_at: UpdatedAt | None

    def __init__(
        self,
        id_: AgentExecutionId,
        node_execution_id: NodeExecutionId,
        created_at: CreatedAt,
        updated_at: UpdatedAt | None = None,
    ) -> None:
        super().__init__(id_)
        self._node_execution_id = node_execution_id
        self._created_at = created_at
        self._updated_at = updated_at

    @classmethod
    def _new(
        cls,
        *,
        id_: AgentExecutionId,
        node_execution_id: NodeExecutionId,
        now: CreatedAt,
    ) -> AgentExecution:
        instance = cls(
            id_=id_,
            node_execution_id=node_execution_id,
            created_at=now,
        )
        instance.append_event(
            AgentExecutionCreatedEvent.now(
                agent_execution_id=instance.id,
                now=now,
            )
        )
        return instance

    @classmethod
    def create(
        cls,
        *,
        id_: AgentExecutionId,
        node_execution_id: NodeExecutionId,
        now: CreatedAt,
    ) -> AgentExecution:
        return cls._new(id_=id_, node_execution_id=node_execution_id, now=now)

    @classmethod
    def restore(
        cls,
        id_: AgentExecutionId,
        node_execution_id: NodeExecutionId,
        created_at: CreatedAt,
        updated_at: UpdatedAt | None = None,
    ) -> Self:
        return cls(
            id_=id_,
            node_execution_id=node_execution_id,
            created_at=created_at,
            updated_at=updated_at,
        )

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._updated_at = UpdatedAt.from_datetime(now.value)
        self.append_event(
            AgentExecutionDeletedEvent.now(
                agentexecution_id=self._id,
                now=CreatedAt.from_datetime(now.value),
            )
        )
    def _update(self, now: UpdatedAt) -> None:
        self._updated_at = now
        self.append_event(
            AgentExecutionUpdatedEvent.now(
                agentexecution_id=self._id,
                now=CreatedAt.from_datetime(now.value),
            )
        )
    @property
    def node_execution_id(self) -> NodeExecutionId:
        return self._node_execution_id

    @property
    def created_at(self) -> CreatedAt | None:
        return self._created_at

    @property
    def updated_at(self) -> UpdatedAt | None:
        return self._updated_at
