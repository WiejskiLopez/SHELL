from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId
from shell.domain.execution.aggregates.workflow.value_objects.workflow_skill_id import WorkflowSkillId
from shell.domain.execution.value_objects.skill_payload import SkillPayload
from shell.domain.platform.base.entity import Entity

if TYPE_CHECKING:
    from datetime import datetime


class WorkflowSkill(Entity[WorkflowSkillId]):
    __slots__ = ("_workflow_id", "_payload", "_created_at")

    def __init__(
        self,
        id: WorkflowSkillId,
        workflow_id: WorkflowId,
        payload: SkillPayload,
        created_at: datetime,
    ) -> None:
        super().__init__(id)
        self._workflow_id = workflow_id
        self._payload = payload
        self._created_at = created_at

    @property
    def workflow_id(self) -> WorkflowId:
        return self._workflow_id

    @property
    def payload(self) -> SkillPayload:
        return self._payload

    @property
    def created_at(self) -> datetime:
        return self._created_at
