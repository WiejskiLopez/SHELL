from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class NodeExecutionStateDeletedIntegrationEvent:
    event_id: str
    occurred_at: datetime
    aggregate_id: str
    aggregate_name: str
    schema_version: int
    node_execution_state_id: str
