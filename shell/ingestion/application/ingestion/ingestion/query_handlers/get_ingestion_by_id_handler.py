from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.ingestion.application.ingestion.ingestion.dto.ingestion import (
        IngestionDto,
    )
    from shell.ingestion.application.ingestion.ingestion.ports.queries.ingestion_query_service import (
        IngestionQueryService,
    )
    from shell.ingestion.application.ingestion.ingestion.queries.get_ingestion_by_id_query import (
        GetIngestionByIdQuery,
    )


class GetIngestionByIdHandler:
    def __init__(self, queries: IngestionQueryService) -> None:
        self._queries = queries

    async def handle(self, query: GetIngestionByIdQuery) -> IngestionDto | None:
        return await self._queries.get_by_id(query.ingestion_id)
