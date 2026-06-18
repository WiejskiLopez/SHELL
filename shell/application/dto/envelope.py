from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class EnvelopeDto:
    id: str
    workflow_id: str
    sender_graph_node_execution_id: str
    receiver_graph_node_execution_id: str
    source_role: str
    target_role: str
    status: str
    stage: str
    step: int
    payload: dict[str, object]
    created_at: datetime
    updated_at: datetime
