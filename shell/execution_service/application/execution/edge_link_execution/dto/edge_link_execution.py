from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class EdgeLinkExecutionDto:
    id: str
    node_execution_id: str
    edge_execution_id: str
    created_at: datetime
    changed_at: datetime | None = None
    deleted_at: datetime | None = None
