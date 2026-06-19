from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.repositories.envelope_repository.envelope_archive import EnvelopeArchive

if TYPE_CHECKING:
    from shell.domain.execution.entities.envelope import Envelope


class SqlEnvelopeArchiveStub(EnvelopeArchive):
    """Stub — archives are stored on filesystem; this is a no-op SQL adapter."""

    async def archive(self, envelope: Envelope) -> str:
        return f"sql://archive/{envelope.id.value}"

    async def get(self, archive_uri: str) -> Envelope | None:
        return None
