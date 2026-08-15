from __future__ import annotations

from pydantic import BaseModel


class CreateIngestionResponse(BaseModel):
    id: str
