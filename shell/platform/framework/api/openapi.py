from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI


OPENAPI_TAGS = [
    {"name": "Users", "description": "User management — CRUD + status lifecycle"},
    {"name": "Sessions", "description": "Session lifecycle — create, list, close, history"},
    {
        "name": "GraphDefinitions",
        "description": "Graph definitions — query by ID or semantic query",
    },
    {"name": "Workflows", "description": "Workflow execution — query workflow status and results"},
    {
        "name": "NodeExecutions",
        "description": "Node execution results — query individual node results",
    },
    {
        "name": "EdgeExecutions",
        "description": "Edge execution — manage edges between nodes in a workflow",
    },
    {"name": "EdgeLinkExecutions", "description": "Edge link execution — link nodes to edges"},
    {"name": "Projects", "description": "Project management — CRUD for projects"},
    {
        "name": "Ingestions",
        "description": "Message router management — CRUD for message routing",
    },
    {
        "name": "SchedulerDefinitions",
        "description": "Scheduler definitions — trigger-based scheduling rules",
    },
    {
        "name": "SchedulerJobs",
        "description": "Scheduler jobs — cyclic APScheduler job configuration",
    },
    {
        "name": "SchedulerExecutions",
        "description": "Scheduler executions — one-shot evaluation results",
    },
    {"name": "Health", "description": "Health monitoring — service liveness and version info"},
]


def configure_openapi(app: FastAPI) -> None:
    app.title = "SHELL Control Plane API"
    app.version = "0.1.0"
    app.description = (
        "SHELL — system execution orchestration API. "
        "Manages users, sessions, graph definitions, workflow execution, "
        "and project resources."
    )
    app.openapi_tags = OPENAPI_TAGS
