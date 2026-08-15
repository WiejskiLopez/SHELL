from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class EdgeExecutionDto:
    id: str
    edge_definition_id: str
    source_node_execution_id: str
    created_at: datetime
    target_node_execution_id: str | None = None
    changed_at: datetime | None = None
