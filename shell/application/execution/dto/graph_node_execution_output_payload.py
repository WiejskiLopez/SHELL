from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class GraphNodeExecutionOutputPayloadDto:
    id: str
    graph_node_execution_id: str
    payload: dict
    is_current: bool
    created_at: datetime
