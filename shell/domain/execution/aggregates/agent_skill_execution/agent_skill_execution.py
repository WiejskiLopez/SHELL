from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.execution.aggregates.agent_skill_execution.value_objects.agent_skill_execution_id import (
    AgentSkillExecutionId,
)
from shell.platform.domain.base.aggregate_root import AggregateRoot

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.agent_execution.value_objects.agent_execution_id import (
        AgentExecutionId,
    )
    from shell.domain.execution.aggregates.agent_skill_execution.value_objects.skill_data import (
        SkillData,
    )
    from shell.platform.domain.value_objects.created_at import CreatedAt

class AgentSkillExecution(AggregateRoot[AgentSkillExecutionId]):
    __slots__ = (
        "_updated_at","_agent_execution_id", "_skill_data", "_created_at")

    _agent_execution_id: AgentExecutionId
    _skill_data: SkillData
    _created_at: CreatedAt

    def __init__(
        self,
        id_: AgentSkillExecutionId,
        agent_execution_id: AgentExecutionId,
        skill_data: SkillData,
        created_at: CreatedAt,
    ) -> None:
        super().__init__(id_)
        self._agent_execution_id = agent_execution_id
        self._skill_data = skill_data
        self._created_at = created_at

    @classmethod
    def restore(
        cls,
        id_: AgentSkillExecutionId,
        agent_execution_id: AgentExecutionId,
        skill_data: SkillData,
        created_at: CreatedAt,
    ) -> Self:
        return cls(
            id_=id_,
            agent_execution_id=agent_execution_id,
            skill_data=skill_data,
            created_at=created_at,
        )

    @classmethod
    def create(
        cls,
        id_: AgentSkillExecutionId,
        agent_execution_id: AgentExecutionId,
        skill_data: SkillData,
        now: CreatedAt,
    ) -> AgentSkillExecution:
        return cls(
            id_=id_,
            agent_execution_id=agent_execution_id,
            skill_data=skill_data,
            created_at=now,
        )

    def _delete(self) -> None:
        raise NotImplementedError("_delete() not yet implemented")

    @property
    def agent_execution_id(self) -> AgentExecutionId:
        return self._agent_execution_id

    @property
    def skill_data(self) -> SkillData:
        return self._skill_data

    @property
    def created_at(self) -> CreatedAt:
        return self._created_at
