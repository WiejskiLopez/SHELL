from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class StartWorkflowCommand:
    task_name: str


@dataclass(frozen=True, slots=True)
class RouteEnvelopesCommand:
    workflow_id: str


@dataclass(frozen=True, slots=True)
class RunTaskerWorkflowCommand:
    task_name: str
    work_dir: str
