from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class RunnerConfigDto:
    id: str
    created_at: datetime
