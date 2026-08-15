from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.execution_service.domain.execution.aggregates.agent_config_execution.events.agent_config_changed_event import (
    AgentConfigChangedEvent,
)
from shell.execution_service.domain.execution.aggregates.agent_config_execution.events.agent_config_execution_created_event import (
    AgentConfigExecutionCreatedEvent,
)
from shell.execution_service.domain.execution.aggregates.agent_config_execution.events.agent_config_execution_deleted_event import (
    AgentConfigExecutionDeletedEvent,
)
from shell.execution_service.domain.execution.aggregates.agent_config_execution.value_objects.agent_config_execution_id import (
    AgentConfigExecutionId,
)
from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.exceptions.domain_error import DomainError
from shell.platform.domain.value_objects.changed_at import NONE_CHANGED_AT, ChangedAt
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt

if TYPE_CHECKING:
    from shell.execution_service.domain.execution.aggregates.agent_execution.value_objects.agent_execution_id import (
        AgentExecutionId,
    )
    from shell.platform.domain.value_objects.config_data import ConfigData
    from shell.platform.domain.value_objects.deleted_at import DeletedAt


class AgentConfigExecution(AggregateRoot[AgentConfigExecutionId]):
    __slots__ = (
        "_created_at",
        "_changed_at",
        "_deleted_at",
        "_agent_execution_id",
        "_config_data",
    )

    _agent_execution_id: AgentExecutionId
    _config_data: ConfigData
    _created_at: CreatedAt
    _changed_at: ChangedAt

    def __init__(
        self,
        *,
        id: AgentConfigExecutionId,
        created_at: CreatedAt,
        changed_at: ChangedAt = NONE_CHANGED_AT,
        agent_execution_id: AgentExecutionId,
        config_data: ConfigData,
    ) -> None:
        super().__init__(id)
        self._agent_execution_id = agent_execution_id
        self._config_data = config_data
        self._created_at = created_at
        self._changed_at = changed_at

    @classmethod
    def create(
        cls,
        id: AgentConfigExecutionId,
        now: CreatedAt,
        agent_execution_id: AgentExecutionId,
        config_data: ConfigData,
    ) -> AgentConfigExecution:
        return cls._new(
            id=id,
            agent_execution_id=agent_execution_id,
            config_data=config_data,
            now=OccurredAt.from_datetime(now.value),
        )

    def change_config(self, config_data: ConfigData, now: OccurredAt) -> None:
        if config_data is None:
            raise DomainError("ConfigData cannot be None")
        self._config_data = config_data
        self._change(now=now)

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now

        self.append_event(
            AgentConfigExecutionDeletedEvent.now(
                agent_config_execution_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def _change(self, now: OccurredAt) -> None:
        self._changed_at = ChangedAt.from_datetime(now.value)
        self.append_event(
            AgentConfigChangedEvent.now(
                agent_config_execution_id=self._id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    @property
    def agent_execution_id(self) -> AgentExecutionId:
        return self._agent_execution_id

    @property
    def config_data(self) -> ConfigData:
        return self._config_data

    @property
    def created_at(self) -> CreatedAt:
        return self._created_at

    @property
    def changed_at(self) -> ChangedAt:
        return self._changed_at

    @classmethod
    def restore(
        cls,
        *,
        id: AgentConfigExecutionId,
        created_at: CreatedAt,
        changed_at: ChangedAt = NONE_CHANGED_AT,
        agent_execution_id: AgentExecutionId,
        config_data: ConfigData,
    ) -> Self:
        return cls(
            id=id,
            agent_execution_id=agent_execution_id,
            config_data=config_data,
            created_at=created_at,
            changed_at=changed_at,
        )

    @classmethod
    def _new(
        cls,
        id: AgentConfigExecutionId,
        now: OccurredAt,
        agent_execution_id: AgentExecutionId,
        config_data: ConfigData,
    ) -> AgentConfigExecution:
        instance = cls(
            id=id,
            agent_execution_id=agent_execution_id,
            config_data=config_data,
            created_at=CreatedAt.from_datetime(now.value),
        )
        instance.append_event(
            AgentConfigExecutionCreatedEvent.now(
                agent_config_execution_id=id,
                now=OccurredAt.from_datetime(now.value),
            )
        )
        return instance
