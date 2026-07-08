from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class AgentExecutionDto:
    id: str
    node_execution_id: str
    created_at: datetime | None = None
