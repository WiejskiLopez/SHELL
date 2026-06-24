from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.agent_execution.value_objects.agent_execution_id import AgentExecutionId
from shell.domain.platform.base.aggregate_root import AggregateRoot

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.execution.aggregates.agent_execution.value_objects.agent_skill_execution_id import (
        AgentSkillExecutionId,
    )
    from shell.domain.execution.aggregates.agent_execution.entities.agent_skill_execution import (
        AgentSkillExecution,
    )
    from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
        GraphNodeExecutionId,
    )
    from shell.domain.execution.value_objects.config import Config
    from shell.domain.execution.value_objects.skill_payload import SkillPayload


class AgentExecution(AggregateRoot[AgentExecutionId]):
    __slots__ = ("_graph_node_execution_id", "_config_snapshot", "_skills")

    _graph_node_execution_id: GraphNodeExecutionId
    _config_snapshot: Config
    _skills: list[AgentSkillExecution]

    def __init__(
        self,
        id_: AgentExecutionId,
        graph_node_execution_id: GraphNodeExecutionId,
        config_snapshot: Config,
    ) -> None:
        super().__init__(id_)
        self._graph_node_execution_id = graph_node_execution_id
        self._config_snapshot = config_snapshot
        self._skills = []

    @classmethod
    def for_node(
        cls,
        id_: AgentExecutionId,
        node_id: GraphNodeExecutionId,
        config_snapshot: Config,
        skills: list[SkillPayload],
        now: datetime,
    ) -> AgentExecution:
        instance = cls(id_, node_id, config_snapshot)
        for payload in skills:
            skill = instance._build_skill(payload, now)
            instance._skills.append(skill)
        return instance

    def add_skill(self, payload: SkillPayload, now: datetime) -> None:
        self._skills.append(self._build_skill(payload, now))

    def _build_skill(
        self,
        payload: SkillPayload,
        now: datetime,
    ) -> AgentSkillExecution:
        from shell.domain.execution.aggregates.agent_execution.value_objects.agent_skill_execution_id import (
            AgentSkillExecutionId,
        )
        from shell.domain.execution.aggregates.agent_execution.entities.agent_skill_execution import (
            AgentSkillExecution,
        )

        return AgentSkillExecution(
            id=AgentSkillExecutionId.generate(),
            agent_execution_id=self._id,
            payload=payload,
            created_at=now,
        )

    @property
    def graph_node_execution_id(self) -> GraphNodeExecutionId:
        return self._graph_node_execution_id

    @property
    def config_snapshot(self) -> Config:
        return self._config_snapshot

    @property
    def skills(self) -> tuple:
        return tuple(self._skills)
