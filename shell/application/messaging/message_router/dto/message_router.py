from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from shell.platform.types import JsonStr


@dataclass(frozen=True, slots=True)
class MessageRouterDto:
    id: str
    message_data: JsonStr
    created_at: datetime | None = None
