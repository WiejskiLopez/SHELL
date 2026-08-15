from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.ingestion.domain.ingestion.aggregates.ingestion.ingestion import (
        Ingestion,
    )
    from shell.ingestion.domain.ingestion.aggregates.ingestion.value_objects.ingestion_id import (
        IngestionId,
    )
    from shell.platform.domain.value_objects.exists_result import ExistsResult


class IngestionRepository(Protocol):
    async def save(self, ingestion: Ingestion) -> None: ...

    async def get_by_id(self, ingestion_id: IngestionId) -> Ingestion | None: ...

    async def delete(self, id: IngestionId) -> None: ...

    async def exists(self, id: IngestionId) -> ExistsResult: ...
