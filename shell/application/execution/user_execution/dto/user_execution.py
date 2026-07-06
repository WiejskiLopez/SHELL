from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class UserExecutionDto:
    id: str
    user_id: str | None = None
    created_at: datetime | None = None
