from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class MessageRouterDto:
    id: str
    message_data: dict[str, Any]
    created_at: datetime | None = None
