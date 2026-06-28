from __future__ import annotations

from shell.domain.execution.aggregates.session_execution.value_objects.session_execution_id import (
    SessionExecutionId,
)
from shell.domain.execution.aggregates.workflow.repositories.workflow_repository import (
    WorkflowRepository,
)
from shell.domain.execution.value_objects.ids import (
    WorkflowId,  # noqa: TC002 — WorkflowId używany w konstruktorach w repozytorium
)
from shell.domain.session.aggregates.session.value_objects.session_id import SessionId
from shell.domain.execution.aggregates.workflow import Workflow
from shell.infrastructure.platform.persistence.in_memory_repository import (
    InMemoryRepository,
)


class InMemoryWorkflowRepository(InMemoryRepository[Workflow, WorkflowId], WorkflowRepository):

    async def get_by_session_id(self, session_id: SessionId) -> list[Workflow]:
        return [
            wf for wf in self._store.values()
            if wf.session_id == session_id
        ]

    async def get_by_session_execution_id(
        self, session_execution_id: SessionExecutionId
    ) -> list[Workflow]:
        return [
            wf for wf in self._store.values()
            if wf.session_execution_id == session_execution_id
        ]
