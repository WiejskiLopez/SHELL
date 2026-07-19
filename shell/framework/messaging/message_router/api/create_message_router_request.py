from __future__ import annotations

from pydantic import BaseModel, Field

from shell.platform.types import JsonStr


class CreateMessageRouterRequest(BaseModel):
    message_data: JsonStr = Field(..., min_length=1)
