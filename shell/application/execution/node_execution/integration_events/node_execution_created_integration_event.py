from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class NodeExecutionCreatedIntegrationEvent:
    event_id: str
    occurred_at: datetime
    aggregate_id: str
    aggregate_name: str
    schema_version: int
    node_execution_id: str
    node_definition_id: str | None
    graph_execution_id: str | None
