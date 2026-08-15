from __future__ import annotations

from pydantic import BaseModel, Field

from shell.platform.types import JsonStr


class CreateIngestionRequest(BaseModel):
    ingestion_data: JsonStr = Field(..., min_length=1)
    ingestion_context: JsonStr = Field(..., min_length=1)
