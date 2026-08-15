from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GetIngestionByIdQuery:
    ingestion_id: str
