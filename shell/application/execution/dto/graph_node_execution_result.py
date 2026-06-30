from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


@dataclass(frozen=True, slots=True)
class GraphNodeExecutionResultDto:
    id: str
    graph_node_execution_id: str
    workflow_id: str
    status: str
    created_at: datetime
    stdout: str | None = None
    stderr: str | None = None
    artifact_uri: str | None = None
