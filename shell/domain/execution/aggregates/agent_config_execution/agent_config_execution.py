from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.execution.aggregates.agent_config_execution.value_objects.agent_config_execution_id import (
    AgentConfigExecutionId,
)
from shell.domain.execution.value_objects.config import Config
from shell.domain.platform.base.aggregate_root import AggregateRoot
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.updated_at import UpdatedAt

if TYPE_CHECKING:
    from shell.domain.session.aggregates.session.value_objects.session_id import SessionId


class AgentConfigExecution(AggregateRoot[AgentConfigExecutionId]):
    __slots__ = ("_session_id", "_config", "_created_at", "_updated_at")

    _session_id: SessionId
    _config: Config
    _created_at: CreatedAt
    _updated_at: UpdatedAt

    def __init__(
        self,
        id: AgentConfigExecutionId,
        session_id: SessionId,
        config: Config,
        created_at: CreatedAt,
        updated_at: UpdatedAt,
    ) -> None:
        super().__init__(id)
        self._session_id = session_id
        self._config = config
        self._created_at = created_at
        self._updated_at = updated_at

    @classmethod
    def restore(
        cls,
        id: AgentConfigExecutionId,
        session_id: SessionId,
        config: Config,
        created_at: CreatedAt,
        updated_at: UpdatedAt,
    ) -> Self:
        return cls(
            id=id,
            session_id=session_id,
            config=config,
            created_at=created_at,
            updated_at=updated_at,
        )

    @classmethod
    def create(
        cls,
        id: AgentConfigExecutionId,
        session_id: SessionId,
        config: Config,
        now: CreatedAt,
    ) -> AgentConfigExecution:
        return cls(
            id=id,
            session_id=session_id,
            config=config,
            created_at=now,
            updated_at=UpdatedAt(now.value),
        )

    def update_config(self, config: Config, now: UpdatedAt) -> None:
        self._config = config
        self._updated_at = now

    @property
    def session_id(self) -> SessionId:
        return self._session_id

    @property
    def config(self) -> Config:
        return self._config

    @property
    def created_at(self) -> CreatedAt:
        return self._created_at

    @property
    def updated_at(self) -> UpdatedAt:
        return self._updated_at
