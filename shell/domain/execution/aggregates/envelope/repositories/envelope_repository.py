from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.envelope import Envelope
    from shell.domain.execution.aggregates.envelope.value_objects.envelope_id import EnvelopeId
    from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId


class EnvelopeRepository(Protocol):
    async def get_by_id(self, envelope_id: EnvelopeId) -> Envelope | None: ...
    async def save(self, envelope: Envelope) -> None: ...
    async def list_by_workflow(
        self, workflow_id: WorkflowId, limit: int | None = None, offset: int = 0
    ) -> list[Envelope]: ...
    async def list_pending(
        self, workflow_id: WorkflowId, limit: int | None = None, offset: int = 0
    ) -> list[Envelope]: ...
