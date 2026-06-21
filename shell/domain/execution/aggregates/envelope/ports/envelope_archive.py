from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.envelope import Envelope


class EnvelopeArchive(Protocol):
    async def archive(self, envelope: Envelope) -> str: ...
    async def get(self, archive_uri: str) -> Envelope | None: ...
