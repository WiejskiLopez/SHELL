from __future__ import annotations

from shell.ingestion.domain.ingestion.aggregates.ingestion.ingestion import Ingestion
from shell.ingestion.domain.ingestion.aggregates.ingestion.repositories.ingestion_repository import (
    IngestionRepository,
)
from shell.ingestion.domain.ingestion.aggregates.ingestion.value_objects.ingestion_id import (
    IngestionId,
)
from shell.platform.infrastructure.persistence.in_memory_repository import InMemoryRepository


class InMemoryIngestionRepository(InMemoryRepository[Ingestion, IngestionId], IngestionRepository):
    pass
