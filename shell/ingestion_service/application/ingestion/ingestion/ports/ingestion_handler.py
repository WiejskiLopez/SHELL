from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.platform.domain.messages import DomainMessage


class IngestionHandler(Protocol):
    async def handle(self, ingestion: DomainMessage) -> None: ...
