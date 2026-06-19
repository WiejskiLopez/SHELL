from __future__ import annotations

from pydantic import BaseModel


class ImportTaskRequest(BaseModel):
    task_execution_name: str
    md_path: str
