from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.ingestion.application.ingestion.ingestion.dto.ingestion import (
        IngestionDto,
    )


class IngestionQueryService(Protocol):
    async def get_by_id(self, ingestion_id: str) -> IngestionDto | None: ...
