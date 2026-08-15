from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class GraphDefinitionResponse(BaseModel):
    id: str
    created_at: datetime
