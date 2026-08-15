from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class IngestionResponse(BaseModel):
    id: str
    ingestion_data: str
    ingestion_context: str
    created_at: datetime
    changed_at: datetime | None = None
    deleted_at: datetime | None = None
