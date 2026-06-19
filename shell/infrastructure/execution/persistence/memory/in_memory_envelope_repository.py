from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.repositories.envelope_repository import EnvelopeRepository
from shell.domain.platform.value_objects.envelope_status import EnvelopeStatus
from shell.domain.platform.value_objects.ids import EnvelopeId

if TYPE_CHECKING:
    from shell.domain.execution.entities.envelope import Envelope
    from shell.domain.platform.value_objects.ids import WorkflowId


class InMemoryEnvelopeRepository(EnvelopeRepository):
    def __init__(self) -> None:
        self._store: dict[str, Envelope] = {}

    async def get_by_id(self, envelope_id: EnvelopeId) -> Envelope | None:
        return self._store.get(envelope_id.value)

    async def save(self, envelope: Envelope) -> None:
        self._store[envelope.id.value] = envelope

    async def list_by_workflow(
        self, workflow_id: WorkflowId, limit: int | None = None, offset: int = 0
    ) -> list[Envelope]:
        results = [envelope for envelope in self._store.values() if envelope.workflow_id == workflow_id]
        results = results[offset:]
        if limit is not None:
            results = results[:limit]
        return results

    async def list_pending(
        self, workflow_id: WorkflowId, limit: int | None = None, offset: int = 0
    ) -> list[Envelope]:
        results = [
            envelope
            for envelope in self._store.values()
            if envelope.workflow_id == workflow_id and envelope.status == EnvelopeStatus.PENDING
        ]
        results = results[offset:]
        if limit is not None:
            results = results[:limit]
        return results
