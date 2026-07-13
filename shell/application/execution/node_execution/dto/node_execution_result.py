from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class NodeExecutionResultDto:
    id: str
    node_execution_id: str
    workflow_id: str
    status: str
    created_at: datetime
    stdout: str | None = None
    stderr: str | None = None
    artifact_uri: str | None = None
