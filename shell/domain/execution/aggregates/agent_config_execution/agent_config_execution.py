from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.execution.aggregates.agent_config_execution.value_objects.agent_config_execution_id import (
    AgentConfigExecutionId,
)
from shell.domain.platform.base.aggregate_root import AggregateRoot
from shell.domain.platform.value_objects.updated_at import UpdatedAt

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.agent_config_execution.value_objects.config import Config
    from shell.domain.execution.aggregates.agent_execution.value_objects.agent_execution_id import (
        AgentExecutionId,
    )
    from shell.domain.execution.aggregates.session_execution.value_objects.session_execution_id import (
        SessionExecutionId,
    )
    from shell.domain.execution.aggregates.user_execution.value_objects.user_execution_id import (
        UserExecutionId,
    )
    from shell.domain.platform.value_objects.created_at import CreatedAt


class AgentConfigExecution(AggregateRoot[AgentConfigExecutionId]):
    __slots__ = (
        "_agent_execution_id",
        "_session_execution_id",
        "_user_execution_id",
        "_config",
        "_created_at",
        "_updated_at",
    )

    _agent_execution_id: AgentExecutionId
    _session_execution_id: SessionExecutionId
    _user_execution_id: UserExecutionId
    _config: Config
    _created_at: CreatedAt
    _updated_at: UpdatedAt

    def __init__(
        self,
        id: AgentConfigExecutionId,
        agent_execution_id: AgentExecutionId,
        session_execution_id: SessionExecutionId,
        user_execution_id: UserExecutionId,
        config: Config,
        created_at: CreatedAt,
        updated_at: UpdatedAt,
    ) -> None:
        super().__init__(id)
        self._agent_execution_id = agent_execution_id
        self._session_execution_id = session_execution_id
        self._user_execution_id = user_execution_id
        self._config = config
        self._created_at = created_at
        self._updated_at = updated_at

    @classmethod
    def restore(
        cls,
        id: AgentConfigExecutionId,
        agent_execution_id: AgentExecutionId,
        session_execution_id: SessionExecutionId,
        user_execution_id: UserExecutionId,
        config: Config,
        created_at: CreatedAt,
        updated_at: UpdatedAt,
    ) -> Self:
        return cls(
            id=id,
            agent_execution_id=agent_execution_id,
            session_execution_id=session_execution_id,
            user_execution_id=user_execution_id,
            config=config,
            created_at=created_at,
            updated_at=updated_at,
        )

    @classmethod
    def create(
        cls,
        id: AgentConfigExecutionId,
        agent_execution_id: AgentExecutionId,
        session_execution_id: SessionExecutionId,
        user_execution_id: UserExecutionId,
        config: Config,
        now: CreatedAt,
    ) -> AgentConfigExecution:
        return cls(
            id=id,
            agent_execution_id=agent_execution_id,
            session_execution_id=session_execution_id,
            user_execution_id=user_execution_id,
            config=config,
            created_at=now,
            updated_at=UpdatedAt(now.value),
        )

    def update_config(self, config: Config, now: UpdatedAt) -> None:
        self._config = config
        self._updated_at = now

    @property
    def agent_execution_id(self) -> AgentExecutionId:
        return self._agent_execution_id

    @property
    def session_execution_id(self) -> SessionExecutionId:
        return self._session_execution_id

    @property
    def user_execution_id(self) -> UserExecutionId:
        return self._user_execution_id

    @property
    def config(self) -> Config:
        return self._config

    @property
    def created_at(self) -> CreatedAt:
        return self._created_at

    @property
    def updated_at(self) -> UpdatedAt:
        return self._updated_at
