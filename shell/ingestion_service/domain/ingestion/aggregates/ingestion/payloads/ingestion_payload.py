"""IngestionPayload — payload produced by the Ingestion aggregate."""

from __future__ import annotations

from dataclasses import dataclass

from shell.ingestion_service.domain.ingestion.aggregates.ingestion.value_objects.ingestion_data import (  # noqa: TC001 -- needed at runtime for deserialization type resolution
    IngestionData,
)
from shell.platform.domain.messages import DomainMessage


@dataclass(frozen=True, slots=True, kw_only=True)
class IngestionPayload(DomainMessage):
    ingestion_data: IngestionData
