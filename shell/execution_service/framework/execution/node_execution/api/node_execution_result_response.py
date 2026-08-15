from __future__ import annotations

from pydantic import BaseModel


class NodeExecutionResultResponse(BaseModel):
    node_execution_id: str
    workflow_id: str
    status: str
    stdout: str | None = None
    stderr: str | None = None
    artifact_uri: str | None = None
    created_at: str | None = None
