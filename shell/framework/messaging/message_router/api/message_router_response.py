from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class MessageRouterResponse(BaseModel):
    id: str
    message_data: str
    message_context: str
    created_at: datetime
    updated_at: datetime | None = None
    deleted_at: datetime | None = None
