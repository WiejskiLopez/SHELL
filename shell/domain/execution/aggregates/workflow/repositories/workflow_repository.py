from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.session.value_objects.session_id import SessionId
    from shell.domain.execution.aggregates.workflow import Workflow
    from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId


class WorkflowRepository(Protocol):
    async def get_by_id(self, workflow_id: WorkflowId) -> Workflow | None: ...
    async def get_by_session_id(self, session_id: SessionId) -> list[Workflow]: ...
    async def save(self, workflow: Workflow) -> None: ...
