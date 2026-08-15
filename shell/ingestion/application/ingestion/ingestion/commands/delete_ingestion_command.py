from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DeleteIngestionCommand:
    ingestion_id: str

    def __post_init__(self) -> None:
        if not self.ingestion_id:
            raise ValueError("ingestion_id cannot be empty")
