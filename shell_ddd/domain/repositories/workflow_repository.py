from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell_ddd.domain.entities.workflow import Workflow
    from shell_ddd.domain.value_objects.ids import WorkflowId


class WorkflowRepository(Protocol):
    async def get_by_id(self, workflow_id: WorkflowId) -> Workflow | None: ...
    async def save(self, workflow: Workflow) -> None: ...
