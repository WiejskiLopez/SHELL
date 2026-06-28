from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.session_execution.value_objects.session_execution_id import (
        SessionExecutionId,
    )
    from shell.domain.execution.aggregates.workflow import Workflow
    from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId
    from shell.domain.platform.value_objects.exists_result import ExistsResult
    from shell.domain.session.aggregates.session.value_objects.session_id import SessionId


class WorkflowRepository(Protocol):
    async def get_by_id(self, workflow_id: WorkflowId) -> Workflow | None: ...
    async def get_by_session_id(self, session_id: SessionId) -> list[Workflow]: ...
    async def get_by_session_execution_id(
        self, session_execution_id: SessionExecutionId
    ) -> list[Workflow]: ...
    async def save(self, workflow: Workflow) -> None: ...
    async def delete(self, id: WorkflowId) -> None: ...
    async def exists(self, id: WorkflowId) -> ExistsResult: ...
    