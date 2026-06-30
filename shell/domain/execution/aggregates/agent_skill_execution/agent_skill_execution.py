from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.execution.aggregates.agent_skill_execution.value_objects.agent_skill_execution_id import (
    AgentSkillExecutionId,
)
from shell.domain.platform.base.aggregate_root import AggregateRoot

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.agent_execution.value_objects.agent_execution_id import (
        AgentExecutionId,
    )
    from shell.domain.execution.value_objects.skill_payload import SkillPayload
    from shell.domain.platform.value_objects.created_at import CreatedAt


class AgentSkillExecution(AggregateRoot[AgentSkillExecutionId]):
    __slots__ = ("_agent_execution_id", "_payload", "_created_at")

    _agent_execution_id: AgentExecutionId
    _payload: SkillPayload
    _created_at: CreatedAt

    def __init__(
        self,
        id_: AgentSkillExecutionId,
        agent_execution_id: AgentExecutionId,
        payload: SkillPayload,
        created_at: CreatedAt,
    ) -> None:
        super().__init__(id_)
        self._agent_execution_id = agent_execution_id
        self._payload = payload
        self._created_at = created_at

    @classmethod
    def restore(
        cls,
        id_: AgentSkillExecutionId,
        agent_execution_id: AgentExecutionId,
        payload: SkillPayload,
        created_at: CreatedAt,
    ) -> Self:
        return cls(
            id_=id_,
            agent_execution_id=agent_execution_id,
            payload=payload,
            created_at=created_at,
        )

    @classmethod
    def create(
        cls,
        id_: AgentSkillExecutionId,
        agent_execution_id: AgentExecutionId,
        payload: SkillPayload,
        now: CreatedAt,
    ) -> AgentSkillExecution:
        return cls(
            id_=id_,
            agent_execution_id=agent_execution_id,
            payload=payload,
            created_at=now,
        )

    @property
    def agent_execution_id(self) -> AgentExecutionId:
        return self._agent_execution_id

    @property
    def payload(self) -> SkillPayload:
        return self._payload

    @property
    def created_at(self) -> CreatedAt:
        return self._created_at
