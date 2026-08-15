from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class NodeExecutionStateDto:
    node_execution_id: str
    status: str
    step: int
    changed_at: datetime
