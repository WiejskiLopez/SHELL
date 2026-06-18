from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class MessageDto:
    id: str
    session_id: str
    correlation_id: str
    sender: str
    receiver: str
    payload: dict[str, object]
    created_at: datetime
