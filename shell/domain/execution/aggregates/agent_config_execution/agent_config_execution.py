from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.execution.aggregates.agent_config_execution.events.agent_config_execution_deleted_event import (
    AgentConfigExecutionDeletedEvent,
)
from shell.domain.execution.aggregates.agent_config_execution.events.agent_config_execution_updated_event import (
    AgentConfigExecutionUpdatedEvent,
)
from shell.domain.execution.aggregates.agent_config_execution.events.agent_config_updated_event import (
    AgentConfigUpdatedEvent,
)
from shell.domain.execution.aggregates.agent_config_execution.value_objects.agent_config_execution_id import (
    AgentConfigExecutionId,
)
from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.exceptions.domain_error import DomainError
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.updated_at import UpdatedAt

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.agent_execution.value_objects.agent_execution_id import (
        AgentExecutionId,
    )
    from shell.platform.domain.value_objects.config_data import ConfigData
    from shell.platform.domain.value_objects.deleted_at import DeletedAt


class AgentConfigExecution(AggregateRoot[AgentConfigExecutionId]):
    __slots__ = (
        "_agent_execution_id",
        "_config_data",
        "_created_at",
        "_updated_at",
        "_deleted_at",
    )

    _agent_execution_id: AgentExecutionId
    _config_data: ConfigData
    _created_at: CreatedAt
    _updated_at: UpdatedAt | None

    def __init__(
        self,
        id: AgentConfigExecutionId,
        agent_execution_id: AgentExecutionId,
        config_data: ConfigData,
        created_at: CreatedAt,
        updated_at: UpdatedAt | None = None,
    ) -> None:
        super().__init__(id)
        self._agent_execution_id = agent_execution_id
        self._config_data = config_data
        self._created_at = created_at
        self._updated_at = updated_at

    @classmethod
    def create(
        cls,
        id: AgentConfigExecutionId,
        agent_execution_id: AgentExecutionId,
        config_data: ConfigData,
        now: CreatedAt,
    ) -> AgentConfigExecution:
        return cls(
            id=id,
            agent_execution_id=agent_execution_id,
            config_data=config_data,
            created_at=now,
            updated_at=UpdatedAt(now.value),
        )

    def update_config(self, config_data: ConfigData, now: UpdatedAt) -> None:
        if config_data is None:
            raise DomainError("ConfigData cannot be None")
        self._config_data = config_data
        self._updated_at = now
        self.append_event(
            AgentConfigUpdatedEvent.now(
                agent_config_execution_id=self._id,
                now=CreatedAt.from_datetime(now.value),
            )
        )

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now

        self.append_event(
            AgentConfigExecutionDeletedEvent.now(
                agent_config_execution_id=self._id,
                now=CreatedAt.from_datetime(now.value),
            )
        )

    def _update(self, now: UpdatedAt) -> None:
        self._updated_at = now
        self.append_event(
            AgentConfigExecutionUpdatedEvent.now(
                agent_config_execution_id=self._id,
                now=CreatedAt.from_datetime(now.value),
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
    def updated_at(self) -> UpdatedAt | None:
        return self._updated_at

    @classmethod
    def restore(
        cls,
        id: AgentConfigExecutionId,
        agent_execution_id: AgentExecutionId,
        config_data: ConfigData,
        created_at: CreatedAt,
        updated_at: UpdatedAt | None = None,
    ) -> Self:
        return cls(
            id=id,
            agent_execution_id=agent_execution_id,
            config_data=config_data,
            created_at=created_at,
            updated_at=updated_at,
        )

    @classmethod
    def _new(
        cls,
        id: AgentConfigExecutionId,
        agent_execution_id: AgentExecutionId,
        config_data: ConfigData,
        now: CreatedAt,
    ) -> AgentConfigExecution:
        return cls(
            id=id,
            agent_execution_id=agent_execution_id,
            config_data=config_data,
            created_at=now,
        )
