from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.session.session_id import SessionId
from shell.domain.execution.aggregates.workflow.ports.workflow_repository import WorkflowRepository
from shell.domain.execution.value_objects.ids import (
    WorkflowId,  # noqa: TC002 — WorkflowId używany w konstruktorach w repozytorium
)

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.workflow import Workflow


class InMemoryWorkflowRepository(WorkflowRepository):
    def __init__(self) -> None:
        self._store: dict[str, Workflow] = {}

    async def get_by_id(self, workflow_id: WorkflowId) -> Workflow | None:
        return self._store.get(workflow_id.value)

    async def get_by_session_id(self, session_id: SessionId) -> list[Workflow]:
        return [
            wf for wf in self._store.values()
            if wf.session_id == session_id
        ]

    async def save(self, workflow: Workflow) -> None:
        self._store[workflow.id.value] = workflow
