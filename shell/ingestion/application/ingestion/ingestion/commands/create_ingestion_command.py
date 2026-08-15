from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateIngestionCommand:
    ingestion_data: str
    ingestion_context: str

    def __post_init__(self) -> None:
        if not self.ingestion_data:
            raise ValueError("ingestion_data cannot be empty")
        if not self.ingestion_context:
            raise ValueError("ingestion_context cannot be empty")
