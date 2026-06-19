from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.repositories.envelope_repository import EnvelopeArchive

if TYPE_CHECKING:
    from shell.domain.execution.entities.envelope import Envelope


class InMemoryEnvelopeArchive(EnvelopeArchive):
    def __init__(self) -> None:
        self._store: dict[str, Envelope] = {}

    async def archive(self, envelope: Envelope) -> str:
        uri = f"memory://archive/{envelope.id.value}"
        self._store[uri] = envelope
        return uri

    async def get(self, archive_uri: str) -> Envelope | None:
        return self._store.get(archive_uri)
