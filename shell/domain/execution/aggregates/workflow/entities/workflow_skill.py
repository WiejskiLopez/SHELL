from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.workflow.workflow_id import WorkflowId
from shell.domain.execution.aggregates.workflow.workflow_skill_id import WorkflowSkillId
from shell.domain.execution.value_objects.skill_payload import SkillPayload

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class WorkflowSkill:
    id: WorkflowSkillId
    workflow_id: WorkflowId
    payload: SkillPayload
    created_at: datetime
