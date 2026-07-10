from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.workflow import Workflow
from shell.domain.execution.aggregates.workflow.repositories.workflow_repository import (
    WorkflowRepository,
)
from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import (
    WorkflowId,  # noqa: TC002 — WorkflowId używany w konstruktorach w repozytorium
)
from shell.platform.infrastructure.persistence.in_memory_repository import (
    InMemoryRepository,
)

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.session_execution.value_objects.session_id_ref import (
        SessionIdRef,
    )


class InMemoryWorkflowRepository(InMemoryRepository[Workflow, WorkflowId], WorkflowRepository):
    async def get_by_session_id(self, session_id: SessionIdRef) -> list[Workflow]:
        return [wf for wf in self._store.values() if wf.session_id == session_id]
