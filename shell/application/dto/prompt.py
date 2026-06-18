from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class PromptDto:
    id: str
    name: str
    version: int
    hash: str
    body: str
    is_current: bool
    created_at: datetime
