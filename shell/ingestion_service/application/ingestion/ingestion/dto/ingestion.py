from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from shell.platform.types import JsonStr


@dataclass(frozen=True, slots=True)
class IngestionDto:
    id: str
    ingestion_data: JsonStr
    ingestion_context: JsonStr
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
