from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_skill_id import (
    GraphExecutionSkillId,
)
from shell.domain.execution.value_objects.skill_payload import SkillPayload

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class GraphExecutionSkill:
    id: GraphExecutionSkillId
    graph_execution_id: GraphExecutionId
    payload: SkillPayload
    created_at: datetime
