from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class EdgeExecutionDto:
    id: str
    edge_definition_id: str
    source_node_execution_id: str
    target_node_execution_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
